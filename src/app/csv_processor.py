# from models import Task as TaskModel
from src.shared.db_models import Task
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime
import pandas as pd  # type: ignore
import os
import traceback


def remove_duplicates(df, params):
    subset = params.get("subset")
    keep = params.get("keep", "first")
    print("subset ", subset)
    print("keep ", keep)
    df = df.drop_duplicates(subset=subset, keep=keep)
    print("removed duplicates")
    return df


def remove_missing_rows(df, params):
    subset = params.get("subset")
    how = params.get("how", "any")
    df = df.dropna(subset=subset, how=how)
    print("removed rows with missing values")
    return df


def drop_columns(df, params):
    columns = params.get("columns")
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
    # add more later...
}


def csv_processing(db: Session):
    task: Task = db.query(Task).filter(
        Task.status == "pending").order_by(Task.created_at).first()
    if not task:
        return None

    task.status = "processing"
    task.started_at = datetime.utcnow()
    task.progress = 0
    db.commit()

    try:
        input_path = task.file_path
        print(f"Processing task {task.id} input={input_path}")

        df = pd.read_csv(input_path)

        ops = []

        if task.config and isinstance(task.config, dict):
            ops = task.config.get("operations", [])
        else:
            ops = []

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

            completed_ops += 1
            task.progress = int((completed_ops / total_ops) * 100)
            db.commit()

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
        task.completed_at = datetime.now()
        db.commit()
    return task
