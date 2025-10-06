from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base

class ClientConfig(Base):
    __tablename__ = "client_configs"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)
    reddit_username = Column(String(255), nullable=True)
    reddit_subreddits = Column(String(2000), nullable=True)  # comma-separated
    keywords = Column(String(2000), nullable=True)  # comma-separated
    is_active = Column(Boolean, default=True)
    
    # Scheduling fields
    scan_interval_minutes = Column(Integer, default=5)  # How often to scan (in minutes)
    scan_start_hour = Column(Integer, default=0)  # Start hour (0-23)
    scan_end_hour = Column(Integer, default=23)  # End hour (0-23)
    scan_days = Column(String(20), default="1,2,3,4,5,6,7")  # Days of week (1=Monday, 7=Sunday)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="configs")




