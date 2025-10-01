import json
import redis
from typing import Any, Optional
from functools import wraps
from app.core.config import settings

# Redis connection
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

def cache_key(prefix: str, *args) -> str:
    """Generate a cache key from prefix and arguments."""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def cache_result(expiry: int = 300, prefix: str = "cache"):
    """Decorator to cache function results in Redis."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = cache_key(f"{prefix}:{func.__name__}", *args, *kwargs.values())
            
            # Try to get from cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(key, expiry, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate cache entries matching a pattern."""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

def get_cache(key: str) -> Optional[Any]:
    """Get value from cache."""
    cached = redis_client.get(key)
    return json.loads(cached) if cached else None

def set_cache(key: str, value: Any, expiry: int = 300):
    """Set value in cache with expiry."""
    redis_client.setex(key, expiry, json.dumps(value, default=str))

