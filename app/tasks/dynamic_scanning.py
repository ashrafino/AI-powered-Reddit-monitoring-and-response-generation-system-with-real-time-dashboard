"""
Dynamic scanning task that respects individual config schedules
"""

from datetime import datetime, timezone, timedelta
from typing import List
import logging

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.config import ClientConfig
from app.tasks.reddit_tasks import scan_reddit

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.reddit_tasks.scan_reddit_dynamic", bind=True)
def scan_reddit_dynamic(self):
    """
    Dynamic scanning that checks each config's schedule and scans accordingly
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting dynamic Reddit scan check")
        
        # Get all active configs
        active_configs = db.query(ClientConfig).filter(ClientConfig.is_active == True).all()
        
        if not active_configs:
            logger.info("No active configs found")
            return {"status": "no_configs", "scanned_configs": 0}
        
        current_time = datetime.now(timezone.utc)
        current_hour = current_time.hour
        current_weekday = current_time.isoweekday()  # 1=Monday, 7=Sunday
        
        configs_to_scan = []
        
        for config in active_configs:
            # Check if current time is within active hours
            start_hour = config.scan_start_hour or 0
            end_hour = config.scan_end_hour or 23
            
            # Handle overnight schedules (e.g., 22:00 to 06:00)
            if start_hour <= end_hour:
                hour_check = start_hour <= current_hour <= end_hour
            else:
                hour_check = current_hour >= start_hour or current_hour <= end_hour
            
            if not hour_check:
                logger.debug(f"Config {config.id}: Outside active hours ({start_hour}-{end_hour})")
                continue
            
            # Check if current day is active
            active_days = config.scan_days or "1,2,3,4,5,6,7"
            active_day_list = [int(d.strip()) for d in active_days.split(',') if d.strip().isdigit()]
            
            if current_weekday not in active_day_list:
                logger.debug(f"Config {config.id}: Not an active day ({current_weekday})")
                continue
            
            # Check if enough time has passed since last scan
            scan_interval = config.scan_interval_minutes or 5
            
            # Get last scan time (you might want to track this in database)
            # For now, we'll use a simple approach based on interval
            minutes_since_hour_start = current_time.minute
            
            # Check if this interval slot should trigger a scan
            if minutes_since_hour_start % scan_interval == 0:
                configs_to_scan.append(config)
                logger.info(f"Config {config.id} scheduled for scan (interval: {scan_interval}min)")
        
        if configs_to_scan:
            # Trigger the main scan task
            logger.info(f"Triggering scan for {len(configs_to_scan)} configs")
            scan_reddit.delay()
            
            return {
                "status": "scan_triggered",
                "scanned_configs": len(configs_to_scan),
                "config_ids": [c.id for c in configs_to_scan]
            }
        else:
            logger.debug("No configs need scanning at this time")
            return {"status": "no_scan_needed", "scanned_configs": 0}
            
    except Exception as e:
        logger.error(f"Dynamic scan check failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()