from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean, Text, Index
from sqlalchemy.orm import relationship

from app.db.base import Base

class MatchedPost(Base):
    __tablename__ = "matched_posts"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)

    subreddit = Column(String(255), index=True)
    reddit_post_id = Column(String(50), unique=True, index=True)
    title = Column(String(1000))
    url = Column(String(1000))
    author = Column(String(255))
    content = Column(Text)
    keywords_matched = Column(String(1000))
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)

    flagged = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    responses = relationship("AIResponse", back_populates="post", cascade="all, delete-orphan")

    # Add composite indexes for better query performance
    __table_args__ = (
        Index('idx_client_created', 'client_id', 'created_at'),
        Index('idx_client_reviewed', 'client_id', 'reviewed'),
        Index('idx_subreddit_created', 'subreddit', 'created_at'),
    )

class AIResponse(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("matched_posts.id", ondelete="CASCADE"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)

    content = Column(Text)
    score = Column(Integer, default=0)

    copied = Column(Boolean, default=False)
    compliance_ack = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("MatchedPost", back_populates="responses")
    
    # Composite indexes for frequently queried columns
    __table_args__ = (
        Index('idx_responses_post_client', 'post_id', 'client_id'),
        Index('idx_responses_client_created', 'client_id', 'created_at'),
        Index('idx_responses_quality_score', 'score'),
    )



