"""
Celery Configuration
Background task queue for asynchronous processing
"""

import logging

from celery import Celery
from kombu import Exchange, Queue

from app.config import settings

_logger = logging.getLogger(__name__)

# Create Celery application
celery_app: Celery = Celery(
    "business_search",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Worker settings
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
    # Result backend settings
    result_expires=settings.TASK_RESULT_EXPIRES,
    result_persistent=False,
    result_compression="gzip",
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Task queues
    task_queues=(
        Queue(
            "default",
            Exchange("default"),
            routing_key="default",
        ),
        Queue(
            "scraping",
            Exchange("scraping"),
            routing_key="scraping",
            priority=5,
        ),
        Queue(
            "processing",
            Exchange("processing"),
            routing_key="processing",
            priority=3,
        ),
    ),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": settings.SCRAPER_MAX_RETRIES},
    task_retry_backoff=True,
    task_retry_backoff_max=600,
    task_retry_jitter=True,
)
