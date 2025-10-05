from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    event_type = Column(String, nullable=False, index=True)
    data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="analytics_events")
    
    # Composite indexes for frequently queried columns
    __table_args__ = (
        Index('idx_analytics_client_date', 'client_id', 'created_at'),
        Index('idx_analytics_client_event', 'client_id', 'event_type'),
        Index('idx_analytics_event_date', 'event_type', 'created_at'),
    )