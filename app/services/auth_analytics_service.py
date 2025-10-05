from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from collections import defaultdict

from app.models.auth_audit import AuthAuditLog
from app.models.user import User


class AuthAnalyticsService:
    """Service for analyzing authentication audit logs and providing security insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_auth_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get authentication statistics for the specified number of days"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Base query for the time period
        base_query = self.db.query(AuthAuditLog).filter(
            AuthAuditLog.created_at >= start_date
        )
        
        # Total events
        total_events = base_query.count()
        
        # Success vs failure counts
        success_count = base_query.filter(AuthAuditLog.success == True).count()
        failure_count = base_query.filter(AuthAuditLog.success == False).count()
        
        # Events by type
        event_types = self.db.query(
            AuthAuditLog.event_type,
            func.count(AuthAuditLog.id).label('count'),
            func.sum(func.cast(AuthAuditLog.success, func.Integer)).label('success_count')
        ).filter(
            AuthAuditLog.created_at >= start_date
        ).group_by(AuthAuditLog.event_type).all()
        
        # Top error codes
        error_codes = self.db.query(
            AuthAuditLog.error_code,
            func.count(AuthAuditLog.id).label('count')
        ).filter(
            and_(
                AuthAuditLog.created_at >= start_date,
                AuthAuditLog.success == False,
                AuthAuditLog.error_code.isnot(None)
            )
        ).group_by(AuthAuditLog.error_code).order_by(desc('count')).limit(10).all()
        
        # Most active users (by successful authentications)
        active_users = self.db.query(
            AuthAuditLog.user_email,
            func.count(AuthAuditLog.id).label('auth_count')
        ).filter(
            and_(
                AuthAuditLog.created_at >= start_date,
                AuthAuditLog.success == True,
                AuthAuditLog.user_email.isnot(None)
            )
        ).group_by(AuthAuditLog.user_email).order_by(desc('auth_count')).limit(10).all()
        
        # Failed login attempts by user
        failed_users = self.db.query(
            AuthAuditLog.user_email,
            func.count(AuthAuditLog.id).label('failure_count')
        ).filter(
            and_(
                AuthAuditLog.created_at >= start_date,
                AuthAuditLog.success == False,
                AuthAuditLog.user_email.isnot(None)
            )
        ).group_by(AuthAuditLog.user_email).order_by(desc('failure_count')).limit(10).all()
        
        # Authentication events by hour (for the last 24 hours)
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        hourly_stats = self.db.query(
            func.date_trunc('hour', AuthAuditLog.created_at).label('hour'),
            func.count(AuthAuditLog.id).label('total'),
            func.sum(func.cast(AuthAuditLog.success, func.Integer)).label('success'),
            func.sum(func.cast(~AuthAuditLog.success, func.Integer)).label('failure')
        ).filter(
            AuthAuditLog.created_at >= last_24h
        ).group_by('hour').order_by('hour').all()
        
        return {
            "period_days": days,
            "total_events": total_events,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round((success_count / total_events * 100) if total_events > 0 else 0, 2),
            "event_types": [
                {
                    "type": event_type,
                    "total": count,
                    "success": success_count,
                    "failure": count - success_count,
                    "success_rate": round((success_count / count * 100) if count > 0 else 0, 2)
                }
                for event_type, count, success_count in event_types
            ],
            "top_error_codes": [
                {"error_code": error_code, "count": count}
                for error_code, count in error_codes
            ],
            "most_active_users": [
                {"user_email": user_email, "auth_count": auth_count}
                for user_email, auth_count in active_users
            ],
            "users_with_failures": [
                {"user_email": user_email, "failure_count": failure_count}
                for user_email, failure_count in failed_users
            ],
            "hourly_stats": [
                {
                    "hour": hour.isoformat(),
                    "total": total,
                    "success": success,
                    "failure": failure
                }
                for hour, total, success, failure in hourly_stats
            ]
        }
    
    def get_user_auth_history(self, user_email: str, days: int = 30) -> Dict[str, Any]:
        """Get authentication history for a specific user"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get user's authentication events
        events = self.db.query(AuthAuditLog).filter(
            and_(
                AuthAuditLog.user_email == user_email,
                AuthAuditLog.created_at >= start_date
            )
        ).order_by(desc(AuthAuditLog.created_at)).all()
        
        # Calculate statistics
        total_events = len(events)
        success_events = [e for e in events if e.success]
        failure_events = [e for e in events if not e.success]
        
        # Group by event type
        events_by_type = defaultdict(list)
        for event in events:
            events_by_type[event.event_type].append(event)
        
        # Recent failures
        recent_failures = [
            {
                "timestamp": event.created_at.isoformat(),
                "event_type": event.event_type,
                "error_code": event.error_code,
                "error_detail": event.error_detail,
                "endpoint": event.endpoint,
                "ip_address": event.ip_address
            }
            for event in failure_events[:10]  # Last 10 failures
        ]
        
        return {
            "user_email": user_email,
            "period_days": days,
            "total_events": total_events,
            "success_count": len(success_events),
            "failure_count": len(failure_events),
            "success_rate": round((len(success_events) / total_events * 100) if total_events > 0 else 0, 2),
            "events_by_type": {
                event_type: len(event_list)
                for event_type, event_list in events_by_type.items()
            },
            "recent_failures": recent_failures,
            "last_successful_auth": success_events[0].created_at.isoformat() if success_events else None,
            "last_failed_auth": failure_events[0].created_at.isoformat() if failure_events else None
        }
    
    def get_security_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security alerts based on authentication patterns"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        alerts = []
        
        # Alert 1: High failure rate for specific users
        high_failure_users = self.db.query(
            AuthAuditLog.user_email,
            func.count(AuthAuditLog.id).label('failure_count')
        ).filter(
            and_(
                AuthAuditLog.created_at >= start_time,
                AuthAuditLog.success == False,
                AuthAuditLog.user_email.isnot(None)
            )
        ).group_by(AuthAuditLog.user_email).having(
            func.count(AuthAuditLog.id) >= 10  # 10+ failures
        ).all()
        
        for user_email, failure_count in high_failure_users:
            alerts.append({
                "type": "high_failure_rate",
                "severity": "high" if failure_count >= 20 else "medium",
                "message": f"User {user_email} has {failure_count} failed authentication attempts",
                "user_email": user_email,
                "count": failure_count,
                "period_hours": hours
            })
        
        # Alert 2: Multiple IPs for same user
        multi_ip_users = self.db.query(
            AuthAuditLog.user_email,
            func.count(func.distinct(AuthAuditLog.ip_address)).label('ip_count')
        ).filter(
            and_(
                AuthAuditLog.created_at >= start_time,
                AuthAuditLog.success == True,
                AuthAuditLog.user_email.isnot(None),
                AuthAuditLog.ip_address.isnot(None)
            )
        ).group_by(AuthAuditLog.user_email).having(
            func.count(func.distinct(AuthAuditLog.ip_address)) >= 3  # 3+ different IPs
        ).all()
        
        for user_email, ip_count in multi_ip_users:
            alerts.append({
                "type": "multiple_ips",
                "severity": "medium",
                "message": f"User {user_email} authenticated from {ip_count} different IP addresses",
                "user_email": user_email,
                "ip_count": ip_count,
                "period_hours": hours
            })
        
        # Alert 3: Unusual authentication times (outside business hours)
        # This is a simplified check - in production you'd want timezone-aware logic
        unusual_time_auths = self.db.query(
            func.count(AuthAuditLog.id).label('count')
        ).filter(
            and_(
                AuthAuditLog.created_at >= start_time,
                AuthAuditLog.success == True,
                or_(
                    func.extract('hour', AuthAuditLog.created_at) < 6,  # Before 6 AM
                    func.extract('hour', AuthAuditLog.created_at) > 22  # After 10 PM
                )
            )
        ).scalar()
        
        if unusual_time_auths and unusual_time_auths > 5:
            alerts.append({
                "type": "unusual_hours",
                "severity": "low",
                "message": f"{unusual_time_auths} successful authentications outside business hours",
                "count": unusual_time_auths,
                "period_hours": hours
            })
        
        return alerts
    
    def get_client_auth_stats(self, client_id: int, days: int = 7) -> Dict[str, Any]:
        """Get authentication statistics for a specific client"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get events for this client
        events = self.db.query(AuthAuditLog).filter(
            and_(
                AuthAuditLog.client_id == client_id,
                AuthAuditLog.created_at >= start_date
            )
        ).all()
        
        # Calculate statistics
        total_events = len(events)
        success_events = [e for e in events if e.success]
        failure_events = [e for e in events if not e.success]
        
        # Unique users
        unique_users = len(set(e.user_email for e in events if e.user_email))
        
        # Most active endpoints
        endpoint_stats = defaultdict(int)
        for event in events:
            if event.endpoint:
                endpoint_stats[event.endpoint] += 1
        
        return {
            "client_id": client_id,
            "period_days": days,
            "total_events": total_events,
            "success_count": len(success_events),
            "failure_count": len(failure_events),
            "success_rate": round((len(success_events) / total_events * 100) if total_events > 0 else 0, 2),
            "unique_users": unique_users,
            "most_active_endpoints": dict(sorted(endpoint_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def search_auth_logs(
        self,
        user_email: Optional[str] = None,
        client_id: Optional[int] = None,
        event_type: Optional[str] = None,
        success: Optional[bool] = None,
        error_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search authentication logs with various filters"""
        
        query = self.db.query(AuthAuditLog)
        
        # Apply filters
        if user_email:
            query = query.filter(AuthAuditLog.user_email.ilike(f"%{user_email}%"))
        if client_id is not None:
            query = query.filter(AuthAuditLog.client_id == client_id)
        if event_type:
            query = query.filter(AuthAuditLog.event_type == event_type)
        if success is not None:
            query = query.filter(AuthAuditLog.success == success)
        if error_code:
            query = query.filter(AuthAuditLog.error_code == error_code)
        if ip_address:
            query = query.filter(AuthAuditLog.ip_address == ip_address)
        if start_date:
            query = query.filter(AuthAuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuthAuditLog.created_at <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        logs = query.order_by(desc(AuthAuditLog.created_at)).offset(offset).limit(limit).all()
        
        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "logs": [
                {
                    "id": log.id,
                    "user_email": log.user_email,
                    "user_id": log.user_id,
                    "client_id": log.client_id,
                    "event_type": log.event_type,
                    "success": log.success,
                    "error_code": log.error_code,
                    "error_detail": log.error_detail,
                    "endpoint": log.endpoint,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "request_id": log.request_id,
                    "session_id": log.session_id,
                    "additional_data": log.additional_data,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ]
        }