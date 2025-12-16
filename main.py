from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, Body
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os
import json
import shutil
from datetime import datetime
from models import ConfigSchema
from db_models import Task, Base
from database import get_db, engine
from csv_processor import csv_processing
import pandas as pd
from fastapi.responses import FileResponse

from fastapi.encoders import jsonable_encoder


app = FastAPI(title="Projo 1")
templates = Jinja2Templates(directory='templates')


@app.on_event("startup")
def on_startup():
    # Creates all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")


@app.get("/health")
def root():
    return {"message": "CSV Processor is online"}


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
def get_task(task_id: str, request: Request, db: Session = Depends(get_db)):
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()
    df = pd.read_csv(task.file_path)
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

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(csv_file.file, buffer)

    # 3. Create task record in database
    db_task = Task(
        id=task_id,
        filename=saved_file,
        original_filename=csv_file.filename,
        status="pending",
        file_path=file_path,
        created_at=datetime.utcnow()
    )

    db.add(db_task)
    db.commit()

    return {"message": "CSV File uploaded", "taskID": task_id}


@app.put("/task/{task_id}")
async def task_configuration(task_id: str,
                             config: ConfigSchema,
                             db: Session = Depends(get_db)
                             ):
    print(config)
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()
    # config_data = json.loads(config)
    # print(config_data)
    # task.config = config_data
    task.config = config.model_dump()
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
    print('download called')
    return FileResponse(
        path=task.result_path,
        media_type="text/csv",
        filename=os.path.basename(task.result_path),
    )
