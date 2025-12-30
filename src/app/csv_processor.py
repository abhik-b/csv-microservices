# from models import Task as TaskModel
from src.shared.db_models import Task
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime
import pandas as pd  # type: ignore
import os
import traceback
from loguru import logger
import sys

logger.add(
    sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss} • {level} • {message}")


def remove_duplicates(df, params):
    subset = params.get("subset")
    keep = params.get("keep", "first")
    print("subset ", subset)
    print("keep ", keep)
    df = df.drop_duplicates(subset=subset, keep=keep)
    logger.info("removed duplicates")
    return df


def remove_missing_rows(df, params):
    subset = params.get("subset")
    how = params.get("how", "any")
    df = df.dropna(subset=subset, how=how)
    logger.info("removed rows with missing values")
    return df


def drop_columns(df, params):
    columns = params.get("columns")
    print("columns ", columns)

    if columns:
        for i in range(len(columns)):
            columns[i] = columns[i].strip()
        df = df.drop(
            columns=[c for c in columns if c in df.columns], errors="ignore")
    logger.info("dropped columns")
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
    task.started_at = datetime.now()
    task.progress = 0
    db.commit()
    logger.info(f"Task Processing began; Progress : {task.progress}% ")

    try:
        input_path = task.file_path
        logger.debug(f"Processing task {task.id} input={input_path}")

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

            handler = OP_REGISTRY.get(op_name)
            logger.debug(f"handler {handler} recieved for {op_name}")
            if not handler:
                raise ValueError(
                    f"No handler registered for operation '{op_name}'")

            df = handler(df, params)
            logger.debug(f"df is updated with handler")

            completed_ops += 1
            task.progress = int((completed_ops / total_ops) * 100)
            db.commit()
            logger.info(f"Task Progress : {task.progress}% ")

        output_path = os.path.join(
            'output', f"processed-{task.original_filename}")
        df.to_csv(output_path, index=False)

        task.result_path = output_path
        task.completed_at = datetime.now()
        task.status = "completed"
        task.progress = 100
        db.commit()
        logger.info(f"Task Processing ends; Progress : {task.progress}% ")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Error processing task:", e)
        task.status = "failed"
        task.error_message = f"{str(e)}\n\n{tb}"
        task.completed_at = datetime.now()
        db.commit()
    return task
