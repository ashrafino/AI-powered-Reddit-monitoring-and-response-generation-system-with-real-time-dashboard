from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.db.session import get_db, get_connection_pool_stats, check_database_health
from app.core.config import settings
from app.models.client import Client
from app.models.post import MatchedPost, AIResponse
from app.models.config import ClientConfig
from app.models.analytics import AnalyticsEvent
import redis
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import socket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health")

@router.get("/")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.app_env,
        "service": "reddit-bot-api"
    }

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness check including database connectivity and connection pool health."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Get connection pool health
        db_health = check_database_health()
        
        # Test Redis connection
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        
        return {
            "status": "ready" if db_health["status"] == "healthy" else "degraded",
            "database": db_health["status"],
            "database_pool": db_health.get("pool_stats", {}),
            "redis": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/live")
def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive", "timestamp": time.time()}

START_TIME = time.time()

@router.get("/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """Comprehensive health check with detailed system information."""
    health_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "reddit-bot-api",
        "version": "1.0.0",
        "environment": settings.app_env,
        "hostname": socket.gethostname()
    }
    
    # Database health with connection pool monitoring
    try:
        db.execute(text("SELECT 1"))
        
        # Get connection pool health
        db_health = check_database_health()
        pool_stats = db_health.get("pool_stats", {})
        
        # Get basic counts
        clients_count = db.query(Client).count()
        posts_count = db.query(MatchedPost).count()
        responses_count = db.query(AIResponse).count()
        configs_count = db.query(ClientConfig).count()
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_posts = db.query(MatchedPost).filter(
            MatchedPost.created_at >= yesterday
        ).count()
        
        recent_responses = db.query(AIResponse).filter(
            AIResponse.created_at >= yesterday
        ).count()
        
        # Calculate pool utilization percentage
        pool_utilization = 0
        if pool_stats.get("pool_size", 0) > 0:
            pool_utilization = (pool_stats.get("checked_out", 0) / 
                              (pool_stats.get("pool_size", 1) + pool_stats.get("max_overflow", 0))) * 100
        
        health_data["database"] = {
            "status": db_health["status"],
            "connectivity": True,
            "connection_pool": {
                "pool_size": pool_stats.get("pool_size", 0),
                "checked_out": pool_stats.get("checked_out", 0),
                "checked_in": pool_stats.get("checked_in", 0),
                "overflow": pool_stats.get("overflow", 0),
                "total_connections": pool_stats.get("total_connections", 0),
                "utilization_percent": round(pool_utilization, 2)
            },
            "clients": clients_count,
            "total_posts": posts_count,
            "total_responses": responses_count,
            "active_configs": configs_count,
            "recent_posts_24h": recent_posts,
            "recent_responses_24h": recent_responses
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_data["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Redis health
    try:
        redis_client = redis.from_url(settings.redis_url)
        ping_result = redis_client.ping()
        
        # Get Redis info
        info = redis_client.info()
        memory_usage = info.get('used_memory', 0)
        max_memory = info.get('maxmemory', 0)
        memory_percent = (memory_usage / max_memory * 100) if max_memory > 0 else 0
        
        health_data["redis"] = {
            "status": "healthy" if ping_result and memory_percent < 80 else "warning",
            "ping": ping_result,
            "memory_usage_mb": memory_usage / (1024**2),
            "memory_percent": memory_percent,
            "connected_clients": info.get('connected_clients', 0),
            "uptime_seconds": info.get('uptime_in_seconds', 0)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_data["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    # System resources
    try:
        # System information
        # Note: Using minimal system info to avoid psutil dependency
        disk_total = os.statvfs('/')
        disk_free = disk_total.f_bavail * disk_total.f_frsize
        disk_size = disk_total.f_blocks * disk_total.f_frsize
        
        health_data["system"] = {
            "status": "healthy",
            "disk_free_gb": disk_free / (1024**3),
            "disk_total_gb": disk_size / (1024**3),
            "disk_usage_percent": (1 - disk_free / disk_size) * 100,
            "start_time": START_TIME,
            "uptime_seconds": time.time() - START_TIME
        }
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        health_data["system"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Calculate overall status
    statuses = []
    for component in ["database", "redis", "system"]:
        if component in health_data:
            statuses.append(health_data[component].get("status", "unknown"))
    
    if "error" in statuses:
        overall_status = "error"
    elif "warning" in statuses:
        overall_status = "warning"
    else:
        overall_status = "healthy"
    
    health_data["overall_status"] = overall_status
    
    return health_data

@router.get("/metrics")
def system_metrics(db: Session = Depends(get_db)):
    """Get system performance metrics."""
    try:
        metrics = {}
        
        # Database metrics
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Get analytics events
        events = db.query(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            AnalyticsEvent.created_at >= yesterday
        ).group_by(AnalyticsEvent.event_type).all()
        
        event_counts = {event_type: count for event_type, count in events}
        
        # Get average response quality
        avg_quality = db.query(func.avg(AIResponse.score)).filter(
            AIResponse.created_at >= yesterday
        ).scalar() or 0
        
        # Get top performing keywords
        top_keywords = db.query(
            MatchedPost.keywords_matched,
            func.count(MatchedPost.id).label('count')
        ).filter(
            MatchedPost.created_at >= yesterday,
            MatchedPost.keywords_matched.isnot(None)
        ).group_by(MatchedPost.keywords_matched).order_by(
            func.count(MatchedPost.id).desc()
        ).limit(5).all()
        
        metrics["performance_24h"] = {
            "events": event_counts,
            "avg_response_quality": round(float(avg_quality), 2),
            "top_keywords": [
                {"keyword": kw, "matches": count} 
                for kw, count in top_keywords if kw
            ]
        }
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        metrics["system_current"] = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Redis metrics
        try:
            redis_client = redis.from_url(settings.redis_url)
            info = redis_client.info()
            
            metrics["redis_current"] = {
                "memory_usage_mb": info.get('used_memory', 0) / (1024**2),
                "connected_clients": info.get('connected_clients', 0),
                "commands_processed": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Redis metrics failed: {e}")
            metrics["redis_current"] = {"error": str(e)}
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )

@router.get("/dependencies")
def check_dependencies():
    """Check external service dependencies."""
    dependencies = {}
    
    # Check OpenAI API
    if settings.openai_api_key:
        try:
            import openai
            openai.api_key = settings.openai_api_key
            # Simple test - just check if key is valid format
            dependencies["openai"] = {
                "status": "configured",
                "api_key_configured": bool(settings.openai_api_key)
            }
        except Exception as e:
            dependencies["openai"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        dependencies["openai"] = {
            "status": "not_configured",
            "api_key_configured": False
        }
    
    # Check Reddit API with actual connection test
    if settings.reddit_client_id and settings.reddit_client_secret:
        try:
            from app.services.reddit_service import test_reddit_connection
            reddit_status = test_reddit_connection()
            dependencies["reddit"] = {
                "status": reddit_status["status"],
                "authenticated": reddit_status["authenticated"],
                "message": reddit_status["message"],
                "client_id_configured": bool(settings.reddit_client_id),
                "client_secret_configured": bool(settings.reddit_client_secret),
                "user_agent_configured": bool(settings.reddit_user_agent),
                "rate_limit": reddit_status.get("rate_limit", {})
            }
        except Exception as e:
            dependencies["reddit"] = {
                "status": "error",
                "error": str(e),
                "client_id_configured": bool(settings.reddit_client_id),
                "client_secret_configured": bool(settings.reddit_client_secret)
            }
    else:
        dependencies["reddit"] = {
            "status": "not_configured",
            "client_id_configured": bool(settings.reddit_client_id),
            "client_secret_configured": bool(settings.reddit_client_secret)
        }
    
    # Check Google Search API
    dependencies["google_search"] = {
        "status": "configured" if settings.serpapi_api_key else "not_configured",
        "api_key_configured": bool(settings.serpapi_api_key)
    }
    
    # Check YouTube API
    dependencies["youtube"] = {
        "status": "configured" if settings.youtube_api_key else "not_configured",
        "api_key_configured": bool(settings.youtube_api_key)
    }
    
    # Check email configuration
    if settings.smtp_host and settings.smtp_user:
        dependencies["email"] = {
            "status": "configured",
            "smtp_configured": True
        }
    else:
        dependencies["email"] = {
            "status": "not_configured",
            "smtp_configured": False
        }
    
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": dependencies
    }

@router.get("/reddit")
def check_reddit_api():
    """Detailed Reddit API health check"""
    try:
        from app.services.reddit_service import test_reddit_connection, validate_subreddit_access
        
        # Test basic connection
        connection_status = test_reddit_connection()
        
        # Test subreddit access with common subreddits
        test_subreddits = ["AskReddit", "technology", "programming"]
        subreddit_tests = {}
        
        for subreddit in test_subreddits:
            try:
                subreddit_tests[subreddit] = validate_subreddit_access(subreddit)
            except Exception as e:
                subreddit_tests[subreddit] = False
                logger.error(f"Error testing subreddit {subreddit}: {e}")
        
        return {
            "status": connection_status["status"],
            "connection": connection_status,
            "subreddit_access_tests": subreddit_tests,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Reddit API health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/database/pool")
def check_connection_pool():
    """Check database connection pool statistics and health."""
    try:
        pool_stats = get_connection_pool_stats()
        db_health = check_database_health()
        
        # Calculate utilization metrics
        total_capacity = pool_stats["pool_size"] + pool_stats["max_overflow"]
        utilization_percent = (pool_stats["checked_out"] / total_capacity * 100) if total_capacity > 0 else 0
        available_connections = pool_stats["checked_in"]
        
        # Determine health status based on utilization
        if utilization_percent > 90:
            status = "critical"
        elif utilization_percent > 75:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "pool_configuration": {
                "pool_size": pool_stats["pool_size"],
                "max_overflow": pool_stats["max_overflow"],
                "total_capacity": total_capacity,
                "timeout_seconds": pool_stats["timeout"]
            },
            "current_usage": {
                "checked_out": pool_stats["checked_out"],
                "checked_in": pool_stats["checked_in"],
                "overflow": pool_stats["overflow"],
                "available": available_connections,
                "utilization_percent": round(utilization_percent, 2)
            },
            "health": db_health["status"],
            "recommendations": get_pool_recommendations(utilization_percent, pool_stats),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Connection pool check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def get_pool_recommendations(utilization: float, stats: dict) -> list:
    """Generate recommendations based on pool utilization."""
    recommendations = []
    
    if utilization > 90:
        recommendations.append("CRITICAL: Connection pool near capacity. Consider increasing pool_size or max_overflow.")
    elif utilization > 75:
        recommendations.append("WARNING: High connection pool utilization. Monitor for potential bottlenecks.")
    
    if stats["overflow"] > 0:
        recommendations.append(f"Using {stats['overflow']} overflow connections. This is normal under load.")
    
    if utilization < 25:
        recommendations.append("Pool utilization is low. Current configuration is adequate.")
    
    return recommendations if recommendations else ["Connection pool is operating normally."]

@router.get("/celery")
def check_celery_health():
    """Check Celery worker and beat health."""
    try:
        from celery import Celery
        
        celery_app = Celery(
            "redditbot",
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend,
        )
        
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        scheduled = inspect.scheduled()
        
        worker_count = len(active_workers) if active_workers else 0
        
        # Check recent task execution
        recent_tasks = 0
        if stats:
            for worker_stats in stats.values():
                recent_tasks += worker_stats.get('total', {}).get('tasks.reddit_tasks.scan_reddit', 0)
        
        return {
            "status": "healthy" if worker_count > 0 else "warning",
            "active_workers": worker_count,
            "worker_details": active_workers or {},
            "worker_stats": stats or {},
            "scheduled_tasks": scheduled or {},
            "recent_scan_tasks": recent_tasks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

