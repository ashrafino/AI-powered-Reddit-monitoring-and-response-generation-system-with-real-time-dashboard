from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.post import MatchedPost, AIResponse
from app.models.analytics import AnalyticsEvent
from app.models.client import Client


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_summary(self, client_id: int) -> Dict:
        """Get dashboard summary for a specific client"""
        # Get posts count for this client
        posts_count = self.db.query(func.count(MatchedPost.id)).filter(
            MatchedPost.client_id == client_id
        ).scalar() or 0
        
        # Get responses count for this client
        responses_count = self.db.query(func.count(AIResponse.id)).join(
            MatchedPost, AIResponse.post_id == MatchedPost.id
        ).filter(MatchedPost.client_id == client_id).scalar() or 0
        
        # Get events for this client
        events_q = self.db.query(
            AnalyticsEvent.event_type, 
            func.count(AnalyticsEvent.id)
        ).filter(
            AnalyticsEvent.client_id == client_id
        ).group_by(AnalyticsEvent.event_type)
        
        events = {etype: count for etype, count in events_q.all()}
        
        return {
            "posts": posts_count,
            "responses": responses_count,
            "events": events,
        }

    def get_performance_trends(self, client_id: int, days: int = 30) -> Dict:
        """Get performance trends for the last N days"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily post counts
        daily_posts = self.db.query(
            func.date(MatchedPost.created_at).label('date'),
            func.count(MatchedPost.id).label('count')
        ).filter(
            and_(
                MatchedPost.client_id == client_id,
                MatchedPost.created_at >= start_date,
                MatchedPost.created_at <= end_date
            )
        ).group_by(func.date(MatchedPost.created_at)).all()
        
        # Get daily response counts
        daily_responses = self.db.query(
            func.date(AIResponse.created_at).label('date'),
            func.count(AIResponse.id).label('count')
        ).join(
            MatchedPost, AIResponse.post_id == MatchedPost.id
        ).filter(
            and_(
                MatchedPost.client_id == client_id,
                AIResponse.created_at >= start_date,
                AIResponse.created_at <= end_date
            )
        ).group_by(func.date(AIResponse.created_at)).all()
        
        return {
            "posts_trend": [{"date": str(date), "count": count} for date, count in daily_posts],
            "responses_trend": [{"date": str(date), "count": count} for date, count in daily_responses],
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()}
        }

    def generate_keyword_insights(self, client_id: int) -> Dict:
        """Generate keyword insights for a client"""
        # This is a simplified version - in a real implementation,
        # you'd analyze post content for keywords
        
        # Get recent posts for this client
        recent_posts = self.db.query(MatchedPost).filter(
            and_(
                MatchedPost.client_id == client_id,
                MatchedPost.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).limit(100).all()
        
        # Simple keyword extraction (in practice, use NLP libraries)
        keywords = {}
        for post in recent_posts:
            if post.title:
                words = post.title.lower().split()
                for word in words:
                    if len(word) > 3:  # Filter short words
                        keywords[word] = keywords.get(word, 0) + 1
        
        # Sort by frequency
        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "top_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
            "total_posts_analyzed": len(recent_posts)
        }

    def track_event(self, client_id: int, event_type: str, data: Optional[Dict] = None):
        """Track an analytics event"""
        event = AnalyticsEvent(
            client_id=client_id,
            event_type=event_type,
            data=data or {},
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()
        return event