from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "redditbot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    # Dynamic Reddit scanning based on config intervals
    "scan-reddit-dynamic": {
        "task": "app.tasks.reddit_tasks.scan_reddit_dynamic",
        "schedule": 60.0,  # Check every minute for configs that need scanning
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

