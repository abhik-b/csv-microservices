from worker.src.celery_app import celery_app
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import os
import traceback
from loguru import logger

# Import your existing modules
from api.src.database import get_db
from shared.db_models import Task
# from src.app.csv_processor import OP_REGISTRY

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


@celery_app.task(
    bind=True,
    name='process_csv_task',
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),  # Auto-retry on any exception
    retry_kwargs={'max_retries': 3}
)
def process_csv_task(self, task_id: str):
    """
    Process CSV file automatically when queued
    """
    logger.info(f"🚀 Starting CSV processing for task: {task_id}")

    # Get database session
    db: Session = next(get_db())

    try:
        # 1. Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # 2. Update status to processing
        task.status = "processing"
        task.started_at = datetime.now()
        task.progress = 10
        db.commit()

        # Update Celery task state

        # Initial progress update
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 5,
                'total': 100,
                'status': 'Starting CSV processing',
                'operation': 'Initializing',
                'current_step': 0,
                'total_steps': 0,
                'task_id': task_id
            }
        )

        # 3. Process CSV (using your existing logic)
        input_path = task.file_path
        df = pd.read_csv(input_path)

        logger.info(f"Read CSV with {len(df)} rows, {len(df.columns)} columns")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 10,
                'total': 100,
                'status': 'CSV file loaded',
                'operation': 'File Reading',
                'current_step': 1,
                'total_steps': 5,
                'task_id': task_id
            }
        )
        # task.progress = 30
        # db.commit()

        # Apply operations from config
        if task.config and isinstance(task.config, dict):
            ops = task.config.get("operations", [])
            total_ops = max(1, len(ops))

            for i, op in enumerate(ops):
                op_name = op.get("op")
                params = op.get("params", {})

                # Send detailed progress update
                self.update_state(
                    state='PROGRESS',
                    meta={
                        # 10-90%
                        'current': int(((i + 1) / max(1, total_ops)) * 80) + 10,
                        'total': 100,
                        'status': f'Applying {op_name}...',
                        'operation': op_name,
                        'current_step': i + 2,  # +2 because step 1 was file reading
                        'total_steps': total_ops + 1,  # +1 for file reading
                        'task_id': task_id,
                        'params': str(params)[:100]  # Truncate long params
                    }
                )
                logger.info(f"Applying operation {i+1}/{total_ops}: {op_name}")
                handler = OP_REGISTRY.get(op_name)
                if not handler:
                    raise ValueError(f"No handler for operation '{op_name}'")

                df = handler(df, params)

                # Update progress for each operation
                progress = 30 + int((i + 1) / total_ops * 60)
                # task.progress = progress
                # db.commit()

        # 4. Save results
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 95,
                'total': 100,
                'status': 'Saving processed file',
                'operation': 'Saving Results',
                'current_step': total_ops + 2,
                'total_steps': total_ops + 2,
                'task_id': task_id
            }
        )
        # task.progress = 90
        # db.commit()

        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)

        output_filename = f"processed_{task.original_filename}"
        output_path = os.path.join('output', output_filename)
        df.to_csv(output_path, index=False)

        # 5. Update task as completed
        task.status = "completed"
        task.completed_at = datetime.now()
        task.result_path = output_path
        task.progress = 100
        db.commit()

        logger.info(f"✅ Task {task_id} completed successfully")

        return {
            "task_id": task_id,
            "status": "completed",
            "result_path": output_path,
            "rows_processed": len(df),
            "columns_processed": len(df.columns)
        }

    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {e}")
        logger.error(traceback.format_exc())

        # Update task as failed
        if 'task' in locals() and task:
            task.status = "failed"
            task.error_message = f"{str(e)}\n\n{traceback.format_exc()}"
            task.completed_at = datetime.now()
            db.commit()

        # Re-raise for Celery retry
        raise e
    finally:
        if 'db' in locals():
            db.close()
