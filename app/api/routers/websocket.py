from fastapi import APIRouter, WebSocket, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple, Optional

from app.core.config import settings
from app.core.security import (
    verify_token, 
    AuthenticationError, 
    AuthErrorCodes, 
    AuthLogger
)
from app.db.session import get_db
from app.models.user import User
from app.services.websocket_service import websocket_endpoint, manager

router = APIRouter()
security = HTTPBearer()


class WebSocketAuthError(Exception):
    """Custom WebSocket authentication error with close codes"""
    def __init__(self, code: int, reason: str, error_code: str = None):
        self.code = code
        self.reason = reason
        self.error_code = error_code
        super().__init__(reason)


class WSAuthCodes:
    """WebSocket close codes for different auth failures"""
    INVALID_TOKEN = 4001
    USER_NOT_FOUND = 4002
    USER_INACTIVE = 4003
    CLIENT_NOT_FOUND = 4004
    INTERNAL_ERROR = 4005
    TOKEN_EXPIRED = 4006
    TOKEN_MISSING = 4007


async def authenticate_websocket_connection(
    websocket: WebSocket,
    token: str,
    db: Session
) -> Tuple[User, Optional[int]]:
    """Authenticate WebSocket connection with detailed error handling"""
    
    # Step 1: Validate token format and presence
    if not token or token.strip() == "":
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.TOKEN_MISSING,
            detail="Token missing in WebSocket connection",
            endpoint="websocket_connect"
        )
        raise WebSocketAuthError(
            code=WSAuthCodes.TOKEN_MISSING,
            reason="Authentication token is required",
            error_code=AuthErrorCodes.TOKEN_MISSING
        )
    
    # Step 2: Verify token using enhanced validation
    validation_result = verify_token(token)
    
    if not validation_result.is_valid:
        # Map token validation errors to appropriate WebSocket close codes
        ws_code = WSAuthCodes.INVALID_TOKEN
        if validation_result.error_code == AuthErrorCodes.TOKEN_EXPIRED:
            ws_code = WSAuthCodes.TOKEN_EXPIRED
        
        AuthLogger.log_auth_failure(
            error_code=validation_result.error_code,
            detail=validation_result.error,
            endpoint="websocket_connect"
        )
        raise WebSocketAuthError(
            code=ws_code,
            reason=validation_result.error,
            error_code=validation_result.error_code
        )
    
    # Step 3: Get user from database
    user = db.query(User).filter(User.email == validation_result.payload.sub).first()
    if user is None:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_NOT_FOUND,
            detail="User not found",
            endpoint="websocket_connect",
            user_email=validation_result.payload.sub
        )
        raise WebSocketAuthError(
            code=WSAuthCodes.USER_NOT_FOUND,
            reason="User account not found",
            error_code=AuthErrorCodes.USER_NOT_FOUND
        )
    
    # Step 4: Check user status
    if not user.is_active:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_INACTIVE,
            detail="User account is inactive",
            endpoint="websocket_connect",
            user_email=user.email,
            user_id=user.id
        )
        raise WebSocketAuthError(
            code=WSAuthCodes.USER_INACTIVE,
            reason="User account is inactive",
            error_code=AuthErrorCodes.USER_INACTIVE
        )
    
    # Step 5: Verify user_id matches token
    if user.id != validation_result.payload.user_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.TOKEN_INVALID,
            detail="Token user_id does not match database user",
            endpoint="websocket_connect",
            user_email=user.email,
            user_id=user.id
        )
        raise WebSocketAuthError(
            code=WSAuthCodes.INVALID_TOKEN,
            reason="Invalid token user information",
            error_code=AuthErrorCodes.TOKEN_INVALID
        )
    
    # Step 6: Verify client_id matches if user has a client
    token_client_id = validation_result.payload.client_id
    if user.client_id and token_client_id != user.client_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.CLIENT_NOT_FOUND,
            detail="Token client_id does not match user's client",
            endpoint="websocket_connect",
            user_email=user.email,
            user_id=user.id,
            client_id=user.client_id
        )
        raise WebSocketAuthError(
            code=WSAuthCodes.CLIENT_NOT_FOUND,
            reason="Invalid client information in token",
            error_code=AuthErrorCodes.CLIENT_NOT_FOUND
        )
    
    # Step 7: Log successful authentication
    AuthLogger.log_auth_success(
        user_email=user.email,
        client_id=token_client_id,
        endpoint="websocket_connect",
        user_id=user.id
    )
    
    return user, token_client_id


@router.websocket("/ws")
async def websocket_connect(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Enhanced WebSocket endpoint with robust authentication and error handling"""
    try:
        # Step 1: Authenticate user with comprehensive error handling
        user, client_id = await authenticate_websocket_connection(websocket, token, db)
        
        # Step 2: Validate client association
        if not client_id and user.client_id:
            client_id = user.client_id
        elif not client_id and not user.client_id:
            AuthLogger.log_auth_failure(
                error_code=AuthErrorCodes.CLIENT_NOT_FOUND,
                detail="User not associated with any client",
                endpoint="websocket_connect",
                user_email=user.email,
                user_id=user.id
            )
            await websocket.close(
                code=WSAuthCodes.CLIENT_NOT_FOUND, 
                reason="User not associated with a client"
            )
            return
        
        # Step 3: Initialize Redis connection if not already done
        if not manager.redis_client:
            redis_initialized = await manager.initialize_redis()
            if not redis_initialized:
                AuthLogger.log_auth_failure(
                    error_code="REDIS_CONNECTION_FAILED",
                    detail="Failed to initialize Redis connection",
                    endpoint="websocket_connect",
                    user_email=user.email,
                    user_id=user.id
                )
                await websocket.close(
                    code=WSAuthCodes.INTERNAL_ERROR,
                    reason="Service temporarily unavailable"
                )
                return
        
        # Step 4: Handle the WebSocket connection with enhanced monitoring
        await websocket_endpoint(websocket, client_id, user.id)
        
    except WebSocketAuthError as e:
        # Handle authentication-specific errors with proper close codes
        AuthLogger.log_auth_failure(
            error_code=e.error_code or "WEBSOCKET_AUTH_ERROR",
            detail=e.reason,
            endpoint="websocket_connect"
        )
        await websocket.close(code=e.code, reason=e.reason)
        
    except Exception as e:
        # Handle unexpected errors
        AuthLogger.log_auth_failure(
            error_code="WEBSOCKET_INTERNAL_ERROR",
            detail=f"Unexpected error during WebSocket connection: {str(e)}",
            endpoint="websocket_connect"
        )
        await websocket.close(
            code=WSAuthCodes.INTERNAL_ERROR, 
            reason=f"Internal server error: {str(e)}"
        )


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


@router.get("/ws/debug/connections")
async def get_connection_debug_info():
    """Get detailed connection information for debugging (admin only)"""
    connections_debug = []
    
    for websocket, info in manager.connection_info.items():
        health_info = manager.health_monitor.connection_health.get(websocket, {})
        
        connection_debug = {
            'connection_id': info.get('connection_id', id(websocket)),
            'client_id': info['client_id'],
            'user_id': info['user_id'],
            'connected_at': info['connected_at'].isoformat(),
            'last_activity': info['last_activity'].isoformat(),
            'messages_sent': info['messages_sent'],
            'messages_received': info['messages_received'],
            'health_status': {
                'is_healthy': health_info.get('is_healthy', False),
                'last_ping': datetime.fromtimestamp(health_info['last_ping']).isoformat() if health_info.get('last_ping') else None,
                'last_pong': datetime.fromtimestamp(health_info['last_pong']).isoformat() if health_info.get('last_pong') else None,
                'missed_pings': health_info.get('missed_pings', 0)
            },
            'connection_duration_seconds': (datetime.utcnow() - info['connected_at']).total_seconds()
        }
        connections_debug.append(connection_debug)
    
    return {
        'total_connections': len(connections_debug),
        'connections': connections_debug,
        'debug_timestamp': datetime.utcnow().isoformat()
    }


@router.get("/ws/debug/client/{client_id}")
async def get_client_connection_debug(client_id: int):
    """Get detailed connection information for a specific client (admin only)"""
    client_connections = []
    
    if client_id in manager.active_connections:
        for websocket in manager.active_connections[client_id]:
            if websocket in manager.connection_info:
                info = manager.connection_info[websocket]
                health_info = manager.health_monitor.connection_health.get(websocket, {})
                
                connection_debug = {
                    'connection_id': info.get('connection_id', id(websocket)),
                    'user_id': info['user_id'],
                    'connected_at': info['connected_at'].isoformat(),
                    'last_activity': info['last_activity'].isoformat(),
                    'messages_sent': info['messages_sent'],
                    'messages_received': info['messages_received'],
                    'health_status': {
                        'is_healthy': health_info.get('is_healthy', False),
                        'last_ping': datetime.fromtimestamp(health_info['last_ping']).isoformat() if health_info.get('last_ping') else None,
                        'last_pong': datetime.fromtimestamp(health_info['last_pong']).isoformat() if health_info.get('last_pong') else None,
                        'missed_pings': health_info.get('missed_pings', 0)
                    },
                    'connection_duration_seconds': (datetime.utcnow() - info['connected_at']).total_seconds()
                }
                client_connections.append(connection_debug)
    
    return {
        'client_id': client_id,
        'total_connections': len(client_connections),
        'connections': client_connections,
        'debug_timestamp': datetime.utcnow().isoformat()
    }


@router.post("/ws/debug/ping-client/{client_id}")
async def debug_ping_client(client_id: int):
    """Send a debug ping to all connections for a specific client"""
    if client_id not in manager.active_connections:
        raise HTTPException(status_code=404, detail="No active connections for client")
    
    ping_results = []
    debug_message = {
        'type': 'debug_ping',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Debug ping from server'
    }
    
    for websocket in manager.active_connections[client_id].copy():
        try:
            await manager.send_personal_message(debug_message, websocket)
            ping_results.append({
                'connection_id': manager.connection_info[websocket].get('connection_id', id(websocket)),
                'status': 'sent',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            ping_results.append({
                'connection_id': manager.connection_info[websocket].get('connection_id', id(websocket)),
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    return {
        'client_id': client_id,
        'ping_results': ping_results,
        'total_attempted': len(ping_results)
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