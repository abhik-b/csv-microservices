# 1. Fast API setup
#   a.basic structure ✅
#   b.Jinja Templates ✅
#   c.Upload Files    ✅
# 2. Set up Sqlite    ✅
# 3. Create Models    ✅
# 4. Task in DB       ✅

from fastapi import FastAPI, Form, File, UploadFile, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
import os
import shutil
from datetime import datetime
from models import Task as TaskModel
from db_models import Task, Base
from database import get_db, engine


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
def home(request: Request):
    return templates.TemplateResponse('home.html', {"request": request})


@app.get("/tasks")
def get_tasks():
    return {"message": "All Tasks"}


@app.get("/task/{task_id}")
def get_task_by_id(task_id: int):
    return {"message": f"Task Id = {task_id}"}


@app.post("/upload")
async def create_task(
    task_type: str = Form(),
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
        task_type=task_type,
        status="pending",
        file_path=file_path,
        created_at=datetime.utcnow()
    )

    db.add(db_task)
    db.commit()

    # 4. Trigger background processing
    csv_processing(db_task)

    return {"message": "CSV File uploaded", "file_path": file_path, "file_name": saved_file}


def csv_processing(task: TaskModel):
    print(f'Fetching file from {task.file_path}')
    print(f'{task.task_type} begins for {task.original_filename}')
