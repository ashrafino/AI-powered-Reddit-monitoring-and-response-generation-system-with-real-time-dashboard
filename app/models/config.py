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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="configs")




