from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.post import MatchedPost, AIResponse
from app.models.analytics import AnalyticsEvent
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics")

@router.get("/summary")
def summary(db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user.role == "admin":
        # Admin sees aggregated data across all clients
        posts_count = db.query(func.count(MatchedPost.id)).scalar() or 0
        responses_count = db.query(func.count(AIResponse.id)).scalar() or 0
        events_q = db.query(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id)).group_by(AnalyticsEvent.event_type)
        events = {etype: count for etype, count in events_q.all()}
        
        return {
            "posts": posts_count,
            "responses": responses_count,
            "events": events,
        }
    else:
        # Client users see enhanced analytics for their client
        if not user.client_id:
            return {"posts": 0, "responses": 0, "events": {}}
            
        analytics_service = AnalyticsService(db)
        return analytics_service.get_dashboard_summary(user.client_id)

@router.get("/trends")
def get_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    if not user.client_id:
        return {"error": "User not associated with a client"}
    
    analytics_service = AnalyticsService(db)
    return analytics_service.get_performance_trends(user.client_id, days)

@router.get("/keywords")
def get_keyword_insights(db: Session = Depends(get_db), user = Depends(get_current_user)):
    if not user.client_id:
        return {"error": "User not associated with a client"}
    
    analytics_service = AnalyticsService(db)
    return analytics_service.generate_keyword_insights(user.client_id)

@router.post("/events")
def track_event(
    event_type: str,
    data: Optional[dict] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    if not user.client_id:
        return {"error": "User not associated with a client"}
    
    analytics_service = AnalyticsService(db)
    analytics_service.track_event(user.client_id, event_type, data)
    return {"status": "success"}



