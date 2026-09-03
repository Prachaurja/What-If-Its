"""Celery application. Broker + result backend are Redis. The worker imports
tasks lazily so it shares the exact same services as the API.
"""
from celery import Celery
from app.core.config import settings

celery = Celery("swipe", broker=settings.redis_url, backend=settings.redis_url,
                include=["app.workers.tasks"])
celery.conf.task_acks_late = True            # re-run a job if the worker dies mid-task
celery.conf.worker_prefetch_multiplier = 1   # one heavy job at a time per worker
celery.conf.task_track_started = True
