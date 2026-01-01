from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import os
import shutil
import pandas as pd
import sys
from datetime import datetime
from loguru import logger
from celery.result import AsyncResult
from pathlib import Path
from contextlib import asynccontextmanager
from shared.schemas import ConfigSchema
from shared.db_models import Task, Base
from src.database import get_db, engine
from worker.src.tasks import process_csv_task



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Runs before the app starts taking requests
    Base.metadata.create_all(bind=engine)
    logger.info("App started 🚀")
    yield
    # Shutdown logic: Runs when the app is stopping
    # (e.g., close DB connections)


app = FastAPI(title="Projo 1", lifespan=lifespan)
templates = Jinja2Templates(directory='templates')
logger.remove()
logger.add(
    sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss} • {level} • {message}")
logger.add(
    Path("/app/logs/app.log"),
    rotation="500 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
    enqueue=True
)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "csv-processor",
        "version": "1.0.0",
        "checks": {}
    }

    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "up"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"down: {str(e)}"

    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        usage = shutil.disk_usage(uploads_dir)

        gb_factor = 1024**3
        health_status["checks"]["disk_space"] = {
            "total_gb": round(usage.total / gb_factor, 2),
            "used_gb": round(usage.used / gb_factor, 2),
            "free_gb": round(usage.free / gb_factor, 2),
            "percent_used": round((usage.used / usage.total) * 100, 2)
        }

        if (usage.used / usage.total) > 0.95:
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["disk_space"] = "directory_not_found"

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


# =====================PAGES===================
@app.get("/admin")
def admin(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return templates.TemplateResponse('admin.html', {"request": request, "tasks": tasks})


@app.get("/")
def homepage(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse('home.html', {"request": request})

@app.get("/tasks/{task_id}")
def get_taskpage(task_id: str, request: Request, db: Session = Depends(get_db)):
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    preview_html = ""
    if task.file_path and os.path.exists(task.file_path):
        try:
            df = pd.read_csv(task.file_path, nrows=5) 
            preview_html = df.to_html(
                classes='table table-striped', index=False)
            logger.info("CSV preview generated successfully")
        except Exception as e:
            logger.warning(f"Could not generate preview: {str(e)}")
            preview_html = "<p>Preview not available</p>"

    celery_status = None

    return templates.TemplateResponse(
        'task.html',
        {
            "request": request,
            "task": task,
            "preview_html": preview_html,
            "celery_status": celery_status
        }
    )

# =====================API ENDPOINTS===================

@app.get("/tasks")
def all_tasks(request: Request, db: Session = Depends(get_db)):
    status_filter = request.query_params.get("")
    query = db.query(Task)
    if status_filter and status_filter in ["processing", "completed", "cancelled", "pending", "failed"]:
        query = query.filter(Task.status == status_filter)
    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@app.get("/task/{task_id}")
async def get_task_by_id(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()
    return task


@app.post("/upload")
async def create_task(
    csv_file: UploadFile = File(),
    db: Session = Depends(get_db)
):

    # 1. Validate file
    if not csv_file.filename.endswith('.csv'):
        return {"error": "Only CSV files are allowed"}

    # 2. Save to filesystem
    task_id = str(uuid.uuid4())
    saved_file = f"{task_id}.csv"
    file_path = os.path.join('uploads', saved_file)
    logger.info(f"File Uploaded successfully : {file_path}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(csv_file.file, buffer)

    # 3. Create task record in database
    db_task = Task(
        id=task_id,
        filename=saved_file,
        original_filename=csv_file.filename,
        status="pending",
        file_path=file_path,
        created_at=datetime.now()
    )

    db.add(db_task)
    db.commit()
    logger.info(f"Task  created successfully;  Task ID: {task_id}")

    return {
        "message": "CSV File uploaded successfully",
        "taskID": task_id,
        "status": "pending",
        "next_step": f"Add configuration at PUT /task/{task_id}",
        "config_url": f"/task/{task_id}"
    }


@app.put("/task/{task_id}")
async def task_configuration(task_id: str,
                             config: ConfigSchema,
                             db: Session = Depends(get_db)
                             ):
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()

    task.config = config.model_dump()
    task.status = "queued"
    logger.info(f"Config for Task {task_id} updated successfully")
    db.commit()
    db.refresh(task)

    try:
        result = process_csv_task.delay(task_id)
        task.celery_task_id = result.id
        db.commit()
        logger.info(
            f"Task {task_id} queued. Celery Task ID: {result.id}")

        return {
            "task": jsonable_encoder(task),
            "message": "Configuration saved and task queued for processing",
            "celery_task_id": result.id,
            "status_url": f"/task/status/{result.id}",
            "progress_url": f"/tasks/{task_id}/progress"
        }

    except Exception as e:
        logger.error(f"Failed to queue task {task_id}: {str(e)}")
        task.status = "pending"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue task: {str(e)}"
        )



@app.get("/tasks/{task_id}/download")
def download_task_result(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    logger.info('download called')
    return FileResponse(
        path=task.result_path,
        media_type="text/csv",
        filename=os.path.basename(task.result_path),
    )


@app.get("/tasks/{task_id}/progress")
def get_task_progress(task_id: str, db: Session = Depends(get_db)):
    # 1. Get task from database
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2. Build response with basic task info
    response = {
        "task_id": task_id,
        "status": task.status,
        "progress": task.progress or 0,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result_path": task.result_path,
        "error_message": task.error_message,
        "celery_task_id": task.celery_task_id,
    }

    # 3. If task has Celery task ID, get detailed status from Celery
    if task.celery_task_id and task.status in ["queued", "processing"]:
        try:
            from worker.src.celery_app import celery_app
            task_result = AsyncResult(task.celery_task_id, app=celery_app)

            response["celery_state"] = task_result.state
            response["celery_ready"] = task_result.ready()

            if task_result.state == 'PROGRESS':
                progress_info = task_result.info or {}
                response.update({
                    "celery_progress": progress_info.get('current', 0),
                    "celery_total": progress_info.get('total', 100),
                    "celery_status": progress_info.get('status', ''),
                    "current_operation": progress_info.get('operation', ''),
                    "current_step": progress_info.get('current_step', 0),
                    "total_steps": progress_info.get('total_steps', 0),
                    "operation_params": progress_info.get('params', '')
                })

                # Update progress from Celery if available
                if 'current' in progress_info:
                    response["progress"] = progress_info['current']

            elif task_result.ready():
                response["celery_result"] = task_result.result

        except Exception as e:
            logger.warning(f"Could not get Celery status: {str(e)}")
            response["celery_error"] = str(e)

    # 4. Update database progress from Celery if needed
    if task.status == "processing" and 'celery_progress' in response:
        # Sync Celery progress to database
        celery_progress = response.get('celery_progress')
        if celery_progress and celery_progress != task.progress:
            task.progress = celery_progress
            db.commit()

    return response
