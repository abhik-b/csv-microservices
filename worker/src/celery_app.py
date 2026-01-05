from celery import Celery
import os

celery_app = Celery(
    'csv_processor',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['worker.src.tasks'] 
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60, 
    task_soft_time_limit=25 * 60,

    # Queue settings
    task_default_queue='csv_processing',

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=100,  # Restart after 100 tasks

    # Retry settings
    task_acks_late=True,  # Don't acknowledge until task completes
    # By default, Celery tells Redis "I got it!" as soon as it picks up the task. But what if the power goes out while processing? The task is lost. acks_late tells Redis: "Wait until I'm actually finished before you delete this task from the queue." If the worker crashes, the task stays in Redis so another worker can try again.
    task_reject_on_worker_lost=True,
    # This works with the one above. If a worker container crashes or disappears, this setting tells Redis to put that task back in the queue immediately so it doesn't get stuck in a "processing" state forever.
)

print(f"✅ Celery configured with broker: {celery_app.conf.broker_url}")
