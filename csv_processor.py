from models import Task as TaskModel
from db_models import Task
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime
import time
import pandas as pd  # type: ignore
import os
import traceback


def remove_duplicates(df, params):
    subset = params.get("subset")  # list or None
    keep = params.get("keep", "first")
    print("subset ", subset)
    print("keep ", keep)
    df = df.drop_duplicates(subset=subset, keep=keep)
    print("removed duplicates")
    return df


def remove_missing_rows(df, params):
    subset = params.get("subset")  # columns to consider, or None -> any
    how = params.get("how", "any")  # 'any' or 'all'
    df = df.dropna(subset=subset, how=how)
    print("removed rows with missing values")
    return df


def drop_columns(df, params):
    columns = params.get("columns")  # list or None
    print("columns ", columns)
    if columns:
        df = df.drop(
            columns=[c for c in columns if c in df.columns], errors="ignore")
    print("dropped columns")
    return df


def fill_missing(df, params):
    if params.get("method") == "constant":
        cols_map = params.get("columns", {})
        for col, val in cols_map.items():
            if col in df.columns:
                df[col] = df[col].fillna(val)
    elif params.get("method") == "mean":
        for col in params.get("columns", []):
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mean())
    return df


# ----- registry -----
OP_REGISTRY = {
    "remove_duplicates": remove_duplicates,
    "remove_missing_rows": remove_missing_rows,
    "drop_columns": drop_columns,
    "fill_missing": fill_missing,
    # add more here...
}
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
            print("isinstance(task.config, dict) failed")

        total_ops = max(1, len(ops))
        completed_ops = 0

        for op in ops:
            op_name = op.get("op")
            params = op.get("params", {})

            print("flag 2")

            handler = OP_REGISTRY.get(op_name)
            if not handler:
                raise ValueError(
                    f"No handler registered for operation '{op_name}'")

            print("flag 3")
            df = handler(df, params)

            # update progress heuristically
            completed_ops += 1
            task.progress = int((completed_ops / total_ops) * 100)
            db.commit()
    # write CSV once at the end
        output_path = os.path.join(
            'output', f"processed-{task.original_filename}")
        df.to_csv(output_path, index=False)

        task.result_path = output_path
        task.completed_at = datetime.utcnow()
        task.status = "completed"
        task.progress = 100
        db.commit()
    except Exception as e:
        tb = traceback.format_exc()
        print("Error processing task:", e)
        task.status = "failed"
        task.error_message = f"{str(e)}\n\n{tb}"
        task.completed_at = datetime.utcnow()
        db.commit()
    return task
