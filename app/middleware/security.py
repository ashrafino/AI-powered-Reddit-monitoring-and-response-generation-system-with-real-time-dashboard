from fastapi import Request, HTTPException
from fastapi.responses import Response
import time
from collections import defaultdict
from typing import Dict, Tuple

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

