from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, JSON, Float, Index
from sqlalchemy.orm import relationship

from app.db.base import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)  # post_matched, response_generated, response_copied, etc.
    data = Column(JSON, nullable=True)  # Additional event data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Add composite indexes for better query performance
    __table_args__ = (
        Index('idx_client_event_created', 'client_id', 'event_type', 'created_at'),
        Index('idx_event_created', 'event_type', 'created_at'),
    )

class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Keyword performance
    keyword = Column(String(255), index=True)
    subreddit = Column(String(255), index=True)
    
    # Metrics
    posts_matched = Column(Integer, default=0)
    responses_generated = Column(Integer, default=0)
    responses_copied = Column(Integer, default=0)
    avg_response_quality = Column(Float, default=0.0)
    avg_post_engagement = Column(Float, default=0.0)  # score + comments
    
    # Time period
    date = Column(DateTime(timezone=True), index=True, nullable=False)
    period_type = Column(String(20), default='daily')  # daily, weekly, monthly
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add composite indexes for better query performance
    __table_args__ = (
        Index('idx_client_date_period', 'client_id', 'date', 'period_type'),
        Index('idx_keyword_date', 'keyword', 'date'),
        Index('idx_subreddit_date', 'subreddit', 'date'),
    )

class TrendAnalysis(Base):
    __tablename__ = "trend_analysis"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Trend data
    topic = Column(String(255), index=True)
    keywords = Column(JSON)  # List of related keywords
    subreddits = Column(JSON)  # List of active subreddits
    
    # Metrics
    activity_score = Column(Float, default=0.0)
    growth_rate = Column(Float, default=0.0)  # Week over week growth
    sentiment_score = Column(Float, default=0.0)
    
    # Time period
    week_start = Column(DateTime(timezone=True), index=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Add composite indexes for better query performance
    __table_args__ = (
        Index('idx_client_week', 'client_id', 'week_start'),
        Index('idx_topic_week', 'topic', 'week_start'),
    )