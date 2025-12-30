from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os
import shutil
from sqlalchemy import text
from datetime import datetime
from src.app.models import ConfigSchema
from src.shared.db_models import Task, Base
from src.app.database import get_db, engine
from src.app.csv_processor import csv_processing
import pandas as pd
from fastapi.responses import FileResponse
from loguru import logger
import sys
from pathlib import Path

from fastapi.encoders import jsonable_encoder
# PROJECT_ROOT = Path(__file__).resolve().parents[0]
# LOG_DIR = PROJECT_ROOT / "logs"

app = FastAPI(title="Projo 1")
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


@app.on_event("startup")
def on_startup():
    # Creates all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (if they didn't exist).")


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "csv-processor",
        "version": "1.0.0",
        "checks": {}
    }

    # 1. Check Database Connection
    try:
        # Use text() for SQLAlchemy 2.0+ compatibility
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "up"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"down: {str(e)}"

    # 2. Check Disk Space for Uploads
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        # returns named tuple: total, used, free (in bytes)
        usage = shutil.disk_usage(uploads_dir)

        # Convert bytes to Gigabytes for readability
        gb_factor = 1024**3
        health_status["checks"]["disk_space"] = {
            "total_gb": round(usage.total / gb_factor, 2),
            "used_gb": round(usage.used / gb_factor, 2),
            "free_gb": round(usage.free / gb_factor, 2),
            "percent_used": round((usage.used / usage.total) * 100, 2)
        }

        # Optional: Set status to unhealthy if disk is > 95% full
        if (usage.used / usage.total) > 0.95:
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["disk_space"] = "directory_not_found"

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


@app.get("/admin")
def admin(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return templates.TemplateResponse('admin.html', {"request": request, "tasks": tasks})


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):

    return templates.TemplateResponse('home.html', {"request": request})


@app.get("/tasks")
def all_tasks(request: Request, db: Session = Depends(get_db)):
    status_filter = request.query_params.get("")
    query = db.query(Task)
    if status_filter and status_filter in ["processing", "completed", "cancelled", "pending", "failed"]:
        query = query.filter(Task.status == status_filter)
    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@app.get("/tasks/{task_id}")
def get_task_page(task_id: str, request: Request, db: Session = Depends(get_db)):
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()
    df = pd.read_csv(task.file_path)
    logger.info("csv read successfully")
    preview_html = df.head().to_html(classes='table table-striped', index=False)
    return templates.TemplateResponse('task.html', {"request": request, "task": task, "preview_html": preview_html})


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

    return {"message": "CSV File uploaded", "taskID": task_id}


@app.put("/task/{task_id}")
async def task_configuration(task_id: str,
                             config: ConfigSchema,
                             db: Session = Depends(get_db)
                             ):
    print(config)
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()

    task.config = config.model_dump()
    logger.info(f"Config for Task {task_id} updated successfully")
    db.commit()
    db.refresh(task)
    return jsonable_encoder(task)


@app.get("/processing")
def get_pending_tasks(db: Session = Depends(get_db)):
    task = csv_processing(db)
    return {'task processed': task.id, 'download_link': task.result_path}


@app.get("/tasks/{task_id}/download")
def download_task_result(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    logger.info('download called')
    return FileResponse(
        path=task.result_path,
        media_type="text/csv",
        filename=os.path.basename(task.result_path),
    )
