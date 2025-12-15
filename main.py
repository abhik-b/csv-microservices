from fastapi import FastAPI, Form, File, UploadFile, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
import os
import json
import shutil
from datetime import datetime
from models import Task as TaskModel
from db_models import Task, Base
from database import get_db, engine
from csv_processor import csv_processing

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


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return templates.TemplateResponse('home.html', {"request": request, "tasks": tasks})


@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    all_tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return all_tasks


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

    return {"message": "CSV File uploaded", "file_path": file_path, "file_name": saved_file}


@app.put("/task/{id}")
async def task_configuration(task_id: str,
                             config=Form(...),
                             db: Session = Depends(get_db)
                             ):
    task = db.query(Task).filter(
        Task.id == task_id).order_by(Task.created_at).first()
    # put task config
    config_data = json.loads(config)
    print(config_data)
    task.config = config_data
    db.commit()
    db.refresh(task)
    return task


@app.get("/processing")
def get_pending_tasks(db: Session = Depends(get_db)):
    task = csv_processing(db)
    return {'task processed': task.id, 'download_link': task.result_path}
