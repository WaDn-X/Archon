"""
Redis-based Caching Service for Zippy Archon

Provides multi-layer caching with Redis for improved performance and reduced database load.
Supports different cache strategies and automatic cache invalidation.
"""

import os
import json
import asyncio
import hashlib
import logging
from typing import Any, Dict, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from .error_service import error_service


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 20
    retry_on_timeout: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    default_ttl: int = 3600  # 1 hour
    max_memory: str = "256mb"
    eviction_policy: str = "allkeys-lru"

    # Performance optimizations
    compression_enabled: bool = True
    pipeline_batch_size: int = 100
    connection_pool_size: int = 10

    # Cache strategies
    use_local_cache: bool = True
    local_cache_size: int = 1000
    cache_warmup_enabled: bool = True


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    hit_rate: float = 0.0
    total_requests: int = 0
    average_response_time: float = 0.0


class CacheKey:
    """Utility class for generating consistent cache keys."""

    @staticmethod
    def generate(
        namespace: str,
        identifier: Union[str, int],
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a consistent cache key."""
        key_parts = [namespace, str(identifier)]

        if params:
            # Sort parameters for consistency
            sorted_params = sorted(params.items())
            param_str = json.dumps(sorted_params, sort_keys=True)
            key_parts.append(hashlib.md5(param_str.encode()).hexdigest()[:8])

        return ":".join(key_parts)

    @staticmethod
    def user_data(user_id: str) -> str:
        """Generate cache key for user data."""
        return f"user:{user_id}"

    @staticmethod
    def project_data(project_id: str) -> str:
        """Generate cache key for project data."""
        return f"project:{project_id}"

    @staticmethod
    def knowledge_items(query_hash: str) -> str:
        """Generate cache key for knowledge search results."""
        return f"knowledge:search:{query_hash}"

    @staticmethod
    def api_response(endpoint: str, params_hash: str) -> str:
        """Generate cache key for API responses."""
        return f"api:{endpoint}:{params_hash}"

    @staticmethod
    def embeddings(text_hash: str) -> str:
        """Generate cache key for text embeddings."""
        return f"embeddings:{text_hash}"


class RedisCacheService:
    """Redis-based caching service with connection pooling and error handling."""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.logger = logging.getLogger(__name__)

        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available. Cache service will operate in memory-only mode.")
            self.redis_client = None
            self.memory_cache: Dict[str, Dict[str, Any]] = {}
            return

        if config is None:
            config = CacheConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD"),
                db=int(os.getenv("REDIS_DB", "0")),
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
                default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
            )

        self.config = config
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = CacheStats()
        self._lock = asyncio.Lock()

        # Initialize Redis client
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Redis client with connection pooling."""
        if not REDIS_AVAILABLE:
            return

        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                health_check_interval=self.config.health_check_interval,
                decode_responses=True
            )
            self.logger.info(f"Redis cache service initialized - {self.config.host}:{self.config.port}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis client: {e}")
            self.redis_client = None

    async def _ensure_connection(self):
        """Ensure Redis connection is available."""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        start_time = asyncio.get_event_loop().time()

        try:
            # Try Redis first
            if await self._ensure_connection():
                value = await self.redis_client.get(key)
                if value is not None:
                    self.stats.hits += 1
                    response_time = asyncio.get_event_loop().time() - start_time
                    self._update_response_time(response_time)
                    return json.loads(value)

            # Fallback to memory cache
            async with self._lock:
                if key in self.memory_cache:
                    cached_item = self.memory_cache[key]
                    if cached_item['expires'] > datetime.now().timestamp():
                        self.stats.hits += 1
                        response_time = asyncio.get_event_loop().time() - start_time
                        self._update_response_time(response_time)
                        return cached_item['value']

            self.stats.misses += 1
            return None

        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            self.stats.errors += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_memory_fallback: bool = True
    ) -> bool:
        """Store value in cache."""
        if ttl is None:
            ttl = self.config.default_ttl

        try:
            serialized_value = json.dumps(value)

            # Try Redis first
            if await self._ensure_connection():
                success = await self.redis_client.setex(key, ttl, serialized_value)
                if success:
                    self.stats.sets += 1
                    return True

            # Fallback to memory cache
            if use_memory_fallback:
                async with self._lock:
                    self.memory_cache[key] = {
                        'value': value,
                        'expires': datetime.now().timestamp() + ttl
                    }
                    self.stats.sets += 1
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            self.stats.errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            deleted = False

            # Delete from Redis
            if await self._ensure_connection():
                result = await self.redis_client.delete(key)
                if result > 0:
                    deleted = True

            # Delete from memory cache
            async with self._lock:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    deleted = True

            if deleted:
                self.stats.deletes += 1

            return deleted

        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            self.stats.errors += 1
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            deleted_count = 0

            # Delete from Redis
            if await self._ensure_connection():
                keys = await self.redis_client.keys(pattern)
                if keys:
                    result = await self.redis_client.delete(*keys)
                    deleted_count += result

            # Delete from memory cache
            async with self._lock:
                keys_to_delete = [
                    key for key in self.memory_cache.keys()
                    if self._matches_pattern(key, pattern)
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                deleted_count += len(keys_to_delete)

            if deleted_count > 0:
                self.stats.deletes += deleted_count

            return deleted_count

        except Exception as e:
            self.logger.error(f"Cache delete pattern error for {pattern}: {e}")
            self.stats.errors += 1
            return 0

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for memory cache."""
        # Convert Redis-style patterns to simple string matching
        if '*' in pattern:
            prefix = pattern.split('*')[0]
            return key.startswith(prefix)
        return key == pattern

    async def clear_all(self) -> bool:
        """Clear all cache entries."""
        try:
            # Clear Redis
            if await self._ensure_connection():
                await self.redis_client.flushdb()

            # Clear memory cache
            async with self._lock:
                self.memory_cache.clear()

            self.logger.info("Cache cleared successfully")
            return True

        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            self.stats.errors += 1
            return False

    async def get_or_set(
        self,
        key: str,
        getter_func: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """Get value from cache or compute and cache it."""
        # Try cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value

        # Compute value
        try:
            value = getter_func()
            if asyncio.iscoroutine(value):
                value = await value

            # Cache the result
            await self.set(key, value, ttl)
            return value

        except Exception as e:
            self.logger.error(f"Error computing value for cache key {key}: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        health_data = {
            "status": "healthy",
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": False,
            "memory_cache_size": len(self.memory_cache),
            "stats": asdict(self.stats)
        }

        if REDIS_AVAILABLE and self.redis_client:
            try:
                await self.redis_client.ping()
                health_data["redis_connected"] = True
                info = await self.redis_client.info()
                health_data["redis_info"] = {
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "uptime_days": info.get("uptime_in_days")
                }
            except Exception as e:
                health_data["status"] = "degraded"
                health_data["redis_error"] = str(e)

        if not health_data["redis_connected"] and not health_data["memory_cache_size"]:
            health_data["status"] = "unhealthy"

        return health_data

    def _update_response_time(self, response_time: float):
        """Update average response time statistic."""
        total_requests = self.stats.hits + self.stats.misses
        if total_requests > 0:
            self.stats.average_response_time = (
                (self.stats.average_response_time * (total_requests - 1) + response_time) /
                total_requests
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.stats.hits + self.stats.misses

        if total_requests > 0:
            self.stats.hit_rate = (self.stats.hits / total_requests) * 100
            self.stats.total_requests = total_requests

        return {
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": self.redis_client is not None,
            "memory_cache_entries": len(self.memory_cache),
            "stats": asdict(self.stats),
            "config": asdict(self.config) if hasattr(self, 'config') else {}
        }

    async def close(self):
        """Close Redis connections and cleanup."""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis cache service closed")

        # Clear memory cache
        async with self._lock:
            self.memory_cache.clear()


# Global cache service instance
_cache_service: Optional[RedisCacheService] = None

def get_cache_service() -> RedisCacheService:
    """Get the global cache service instance."""
    global _cache_service

    if _cache_service is None:
        _cache_service = RedisCacheService()

    return _cache_service

# Cache decorators for easy use
def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(arg) for arg in args if arg is not None])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None])

            cache_key = ":".join(key_parts)

            # Try cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Decorator to invalidate cache entries after function execution."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Execute function first
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache = get_cache_service()
            await cache.delete_pattern(pattern)

            return result

        return wrapper
    return decorator
