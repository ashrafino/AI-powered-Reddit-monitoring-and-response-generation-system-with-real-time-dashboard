from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "redditbot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    # Reddit scanning every 5 minutes
    "scan-reddit-every-5-min": {
        "task": "app.tasks.reddit_tasks.scan_reddit",
        "schedule": 300.0,
    },
    # Update performance metrics daily at 1 AM
    "update-performance-metrics-daily": {
        "task": "app.tasks.reddit_tasks.update_performance_metrics",
        "schedule": 86400.0,  # 24 hours
    },
    # Generate trend analysis weekly (every 7 days)
    "generate-trend-analysis-weekly": {
        "task": "app.tasks.reddit_tasks.generate_trend_analysis",
        "schedule": 604800.0,  # 7 days
    },
    # Cleanup old data weekly
    "cleanup-old-data-weekly": {
        "task": "app.tasks.reddit_tasks.cleanup_old_data",
        "schedule": 604800.0,  # 7 days
    },
}

celery_app.autodiscover_tasks(["app.tasks"])

# Manually import tasks to ensure they're registered
from app.tasks import reddit_tasks

