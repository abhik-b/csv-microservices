from models import Task as TaskModel
from db_models import Task
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime
import time
import pandas as pd  # type: ignore
import os
import traceback


def remove_duplicates(df, filename: str):
    df = df.drop_duplicates()
    print("Removed duplicates")
    output_path = os.path.join('output', f"rm-duplicates-{filename}")
    df.to_csv(output_path, index=False)
    print(f"file saved to {output_path}")
    return df, output_path


def remove_missing_rows(df, filename: str):
    df = df.drop_duplicates()
    print("Removed Missing rows")
    output_path = os.path.join('output', f"rm-missed-rows-{filename}")
    df.to_csv(output_path, index=False)
    print(f"file saved to {output_path}")
    return df, output_path

# FIX THE OUTPUT PATH


def validate_data():
    pass


def calculate_statistics():
    pass


def format_columns():
    pass


# def csv_processing(db: Session):
#     task = db.query(Task).filter(Task.status == "pending").first()
#     print(f'Fetching file from {task.file_path}')
#     task.status = "processing"
#     task.started_at = datetime.utcnow()
#     df = pd.read_csv(task.file_path)
#     try:
#         for task_type in task.task_type:
#             match task_type:
#                 case "remove_duplicates":
#                     print(f'Removing Duplicates')
#                     df, output_path = remove_duplicates(
#                         df, task.original_filename)
#                     task.result_path = output_path
#                 case "remove_missing_rows":
#                     print(f'Removing Rows with missing values')
#                     df, output_path = remove_missing_rows(
#                         task.file_path, task.original_filename)
#                     task.result_path = output_path
#         task.completed_at = datetime.utcnow()
#         task.status = "completed"
#     except:
#         task.status = "failed"
#     finally:
#         db.commit()
#     return task

def csv_processing(db: Session):
    # Atomically fetch the next pending task (simple approach)
    task: Task = db.query(Task).filter(
        Task.status == "pending").order_by(Task.created_at).first()
    if not task:
        return None

    task.status = "processing"
    task.started_at = datetime.utcnow()
    task.progress = 0
    db.commit()  # persist started state

    try:
        input_path = task.file_path
        print(f"Processing task {task.id} input={input_path}")

        # Read CSV - infer dtypes; consider reading chunked for large files.
        df = pd.read_csv(input_path)

        # load operations from config
        ops = []
        if task.config and isinstance(task.config, dict):
            ops = task.config.get("operations", [])
        else:
            # Backwards compat: maybe task.task_type existed as list of strings
            # but we removed it. If you kept it, handle here.
            ops = []

        total_ops = max(1, len(ops))
        completed_ops = 0
    except Exception as e:
        tb = traceback.format_exc()
        print("Error processing task:", e)
        task.status = "failed"
        task.error_message = f"{str(e)}\n\n{tb}"
        task.completed_at = datetime.utcnow()
        db.commit()
    return task
