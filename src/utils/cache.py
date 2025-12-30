"""
Caching utilities for performance optimization
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
from functools import wraps
from datetime import timedelta

class RedisCache:
    """Redis-based caching"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        if not self._redis:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._redis:
            await self.connect()
        
        value = await self._redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        if not self._redis:
            await self.connect()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await self._redis.set(key, value, ex=ttl)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries by pattern"""
        if not self._redis:
            await self.connect()
        
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)

def cache_response(ttl: int = 300):
    """Decorator to cache function responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cache = RedisCache()
            cached = await cache.get(cache_key)
            
            if cached is not None:
                return cached
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator
