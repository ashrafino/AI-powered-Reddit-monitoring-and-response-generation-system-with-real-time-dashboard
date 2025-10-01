from fastapi import APIRouter, WebSocket, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.websocket_service import websocket_endpoint, manager

router = APIRouter()
security = HTTPBearer()


async def get_user_from_token(token: str, db: Session) -> User:
    """Extract user from JWT token for WebSocket authentication"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.websocket("/ws")
async def websocket_connect(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time updates"""
    try:
        # Authenticate user from token
        user = await get_user_from_token(token, db)
        
        if not user.client_id:
            await websocket.close(code=1008, reason="User not associated with a client")
            return
        
        # Initialize Redis connection if not already done
        if not manager.redis_client:
            await manager.initialize_redis()
        
        # Handle the WebSocket connection
        await websocket_endpoint(websocket, user.client_id, user.id)
        
    except Exception as e:
        await websocket.close(code=1011, reason=f"Authentication failed: {str(e)}")


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get comprehensive WebSocket connection statistics"""
    return manager.get_connection_stats()


@router.get("/ws/monitoring-status")
async def get_monitoring_status():
    """Get monitoring status for dashboard display"""
    return manager.get_monitoring_status()


@router.get("/ws/health")
async def get_websocket_health():
    """Get WebSocket service health information"""
    stats = manager.get_connection_stats()
    health_stats = manager.health_monitor.get_health_stats()
    
    return {
        "service_status": "healthy" if stats['current_connections'] >= 0 else "error",
        "redis_connected": stats['redis_status']['connected'],
        "total_connections": stats['current_connections'],
        "healthy_connections": health_stats['healthy_connections'],
        "unhealthy_connections": health_stats['unhealthy_connections'],
        "health_percentage": health_stats['health_percentage'],
        "uptime_seconds": stats['lifetime_stats']['uptime_seconds'],
        "last_updated": datetime.utcnow().isoformat()
    }


@router.post("/ws/broadcast")
async def broadcast_message(
    message: dict,
    client_id: int = None,
    db: Session = Depends(get_db)
):
    """Broadcast a message to WebSocket clients (admin only)"""
    # This endpoint would typically require admin authentication
    # For now, it's a simple broadcast mechanism
    
    if client_id:
        await manager.broadcast_to_client(message, client_id)
    else:
        await manager.broadcast_to_all(message)
    
    return {"status": "Message broadcasted successfully"}


@router.post("/ws/test-connection")
async def test_websocket_connection():
    """Test WebSocket service connectivity"""
    try:
        # Initialize Redis if not connected
        if not manager.redis_client:
            await manager.initialize_redis()
        
        # Test Redis connection
        if manager.redis_client:
            await manager.redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "disconnected"
        
        return {
            "status": "success",
            "websocket_service": "running",
            "redis_status": redis_status,
            "active_connections": manager.get_connection_stats()['current_connections'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }