#!/usr/bin/env python3
"""
Database migration script to add performance indexes.
This script adds composite indexes to improve query performance.
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_indexes():
    """Add performance indexes to the database."""
    engine = create_engine(settings.database_url)
    
    indexes = [
        # MatchedPost indexes (already in model, but adding for existing databases)
        "CREATE INDEX IF NOT EXISTS idx_client_created ON matched_posts(client_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_client_reviewed ON matched_posts(client_id, reviewed)",
        "CREATE INDEX IF NOT EXISTS idx_subreddit_created ON matched_posts(subreddit, created_at)",
        
        # AIResponse indexes
        "CREATE INDEX IF NOT EXISTS idx_responses_post_client ON ai_responses(post_id, client_id)",
        "CREATE INDEX IF NOT EXISTS idx_responses_client_created ON ai_responses(client_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_responses_quality_score ON ai_responses(score)",
        
        # AnalyticsEvent indexes
        "CREATE INDEX IF NOT EXISTS idx_analytics_client_date ON analytics_events(client_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_client_event ON analytics_events(client_id, event_type)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_event_date ON analytics_events(event_type, created_at)",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                logger.info(f"Creating index: {index_sql}")
                conn.execute(text(index_sql))
                conn.commit()
                logger.info("✓ Index created successfully")
            except Exception as e:
                logger.error(f"✗ Failed to create index: {e}")
                conn.rollback()
    
    logger.info("Index creation complete!")


if __name__ == "__main__":
    logger.info("Starting database index migration...")
    add_indexes()
    logger.info("Migration complete!")
