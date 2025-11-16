"""
Celery worker configuration
Connects to Redis broker and result backend for async task processing
"""

from celery import Celery
from app.config import settings

# Initialize Celery instance
celery_app = Celery(
    "klipnote",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]  # Auto-discover tasks from app.tasks module
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task result expiration (24 hours)
    result_expires=86400,
    # Task acknowledgment
    task_acks_late=True,
    # Worker configuration
    worker_prefetch_multiplier=1,  # Only fetch one task at a time (important for long-running GPU tasks)
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks to prevent memory leaks

    # Epic 4: Multi-Worker Queue Routing
    # Routes tasks to model-specific worker queues based on queue parameter
    # Usage: transcribe_audio.apply_async(args=[...], queue="belle2")
    task_routes={
        # Default routing (can be overridden by explicit queue parameter)
        "app.tasks.transcribe_audio": {"queue": "default"},
    },

    # Define available queues
    # Workers subscribe to specific queues via --queue parameter
    task_queues={
        "belle2": {
            "exchange": "belle2",
            "routing_key": "belle2",
        },
        "whisperx": {
            "exchange": "whisperx",
            "routing_key": "whisperx",
        },
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
    },
)
