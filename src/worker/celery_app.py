from celery import Celery
import os

# Create Celery app
celery_app = Celery(
    'csv_processor',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['src.worker.tasks']  # Path to tasks
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,

    # Queue settings
    task_default_queue='csv_processing',

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=100,  # Restart after 100 tasks

    # Retry settings
    task_acks_late=True,  # Don't acknowledge until task completes
    task_reject_on_worker_lost=True,
)

print(f"✅ Celery configured with broker: {celery_app.conf.broker_url}")
