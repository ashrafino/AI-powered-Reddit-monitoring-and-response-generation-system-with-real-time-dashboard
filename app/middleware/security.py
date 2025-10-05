from fastapi import Request, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
import uuid

# Simple in-memory rate limiter (use Redis in production)
rate_limit_storage: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0, 0))

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Rate limiting decorator."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            current_time = time.time()
            
            # Clean old entries
            if current_time - rate_limit_storage[client_ip][0] > window_seconds:
                rate_limit_storage[client_ip] = (current_time, 0)
            
            request_time, request_count = rate_limit_storage[client_ip]
            
            if current_time - request_time <= window_seconds:
                if request_count >= max_requests:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Please try again later."
                    )
                rate_limit_storage[client_ip] = (request_time, request_count + 1)
            else:
                rate_limit_storage[client_ip] = (current_time, 1)
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def add_security_headers(response: Response):
    """Add security headers to response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


class ClientScopedQueryFilter:
    """Middleware for enforcing client data isolation at the database level"""
    
    @staticmethod
    def filter_by_client(query, client_id: Optional[int], model_class):
        """Filter query by client_id if the model has a client_id field"""
        if hasattr(model_class, 'client_id') and client_id is not None:
            return query.filter(model_class.client_id == client_id)
        return query
    
    @staticmethod
    def validate_client_access(obj, client_id: Optional[int], user_role: str = "client"):
        """Validate that user can access the object based on client scoping"""
        if user_role == "admin":
            return True  # Admins can access all data
            
        if hasattr(obj, 'client_id'):
            return obj.client_id == client_id
        return True  # If no client_id field, allow access


def generate_request_id() -> str:
    """Generate a unique request ID for tracking"""
    return str(uuid.uuid4())


def extract_client_info(request: Request) -> Dict[str, Optional[str]]:
    """Extract client information from request for audit logging"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "request_id": getattr(request.state, "request_id", None)
    }

