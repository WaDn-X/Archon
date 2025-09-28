"""
Enhanced Client Manager with Connection Pooling and Retry Logic

Provides resilient database connections with automatic retry, connection pooling,
and comprehensive error handling for improved reliability.
"""

import os
import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable, TypeVar
from contextlib import asynccontextmanager
from dataclasses import dataclass

from supabase import Client, create_client

from .error_service import error_service

T = TypeVar('T')

@dataclass
class ConnectionConfig:
    """Database connection configuration."""
    url: str
    key: str
    max_pool_size: int = 10
    min_pool_size: int = 2
    max_idle_time: int = 300  # 5 minutes
    max_lifetime: int = 3600  # 1 hour
    retry_attempts: int = 3
    retry_delay: float = 0.5
    retry_backoff: float = 2.0
    connection_timeout: float = 10.0
    command_timeout: float = 30.0

@dataclass
class ConnectionStats:
    """Connection pool statistics."""
    active_connections: int = 0
    idle_connections: int = 0
    total_connections_created: int = 0
    total_connections_closed: int = 0
    total_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    last_health_check: Optional[float] = None
    health_check_failures: int = 0

class ConnectionPool:
    """Manages a pool of database connections."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Connection pool
        self._pool: Dict[str, Client] = {}
        self._active_count = 0
        self._stats = ConnectionStats()
        self._lock = asyncio.Lock()

    async def get_connection(self) -> Client:
        """Get a connection from the pool."""
        async with self._lock:
            # Try to reuse an existing connection
            if self._pool:
                connection_id, client = next(iter(self._pool.items()))
                del self._pool[connection_id]
                self._stats.idle_connections -= 1
                self._stats.active_connections += 1
                return client

            # Create new connection if pool is not full
            if self._active_count < self.config.max_pool_size:
                client = await self._create_connection()
                self._active_count += 1
                self._stats.total_connections_created += 1
                return client

            # Wait for a connection to become available
            raise RuntimeError("Connection pool exhausted")

    async def return_connection(self, client: Client):
        """Return a connection to the pool."""
        async with self._lock:
            if self._active_count > 0:
                connection_id = id(client)
                self._pool[str(connection_id)] = client
                self._stats.active_connections -= 1
                self._stats.idle_connections += 1

    async def _create_connection(self) -> Client:
        """Create a new database connection."""
        try:
            client = create_client(
                self.config.url,
                self.config.key,
                options={
                    "pool": {
                        "min": self.config.min_pool_size,
                        "max": self.config.max_pool_size,
                    }
                }
            )

            self.logger.info(f"Created new Supabase connection (pool size: {self._active_count + 1})")
            return client

        except Exception as e:
            self.logger.error(f"Failed to create database connection: {e}")
            raise

    async def close_all(self):
        """Close all connections in the pool."""
        async with self._lock:
            for client in self._pool.values():
                # Supabase client handles connection closing internally
                pass

            self._pool.clear()
            self._active_count = 0
            self._stats.idle_connections = 0
            self.logger.info("Closed all database connections")

    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics."""
        return self._stats

class RetryPolicy:
    """Configures retry behavior for database operations."""

    def __init__(self, max_attempts: int = 3, base_delay: float = 0.5, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        return self.base_delay * (self.backoff_factor ** attempt)

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class EnhancedSupabaseClient:
    """Enhanced Supabase client with pooling and retry logic."""

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.logger = logging.getLogger(__name__)

        if config is None:
            config = ConnectionConfig(
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_SERVICE_KEY", "")
            )

        if not config.url or not config.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

        self.config = config
        self.connection_pool = ConnectionPool(config)
        self.retry_policy = RetryPolicy(
            max_attempts=config.retry_attempts,
            base_delay=config.retry_delay,
            backoff_factor=config.retry_backoff
        )

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for getting a database connection."""
        client = await self.connection_pool.get_connection()
        try:
            yield client
        finally:
            await self.connection_pool.return_connection(client)

    async def execute_with_retry(
        self,
        operation: Callable[[Client], T],
        operation_name: str = "database_operation"
    ) -> T:
        """Execute a database operation with automatic retry."""
        last_exception = None

        for attempt in range(self.retry_policy.max_attempts):
            try:
                async with self.get_connection() as client:
                    start_time = time.time()
                    result = operation(client)
                    response_time = time.time() - start_time

                    # Update stats
                    self.connection_pool._stats.total_operations += 1
                    self.connection_pool._stats.average_response_time = (
                        (self.connection_pool._stats.average_response_time *
                         (self.connection_pool._stats.total_operations - 1) +
                         response_time) / self.connection_pool._stats.total_operations
                    )

                    return result

            except Exception as e:
                last_exception = e
                self.connection_pool._stats.failed_operations += 1

                if attempt < self.retry_policy.max_attempts - 1:
                    delay = self.retry_policy.get_delay(attempt)
                    self.logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.retry_policy.max_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"{operation_name} failed after {self.retry_policy.max_attempts} attempts: {e}"
                    )

        # All retries exhausted
        raise DatabaseError(f"{operation_name} failed after {self.retry_policy.max_attempts} attempts") from last_exception

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform a SELECT query with retry logic."""

        def operation(client: Client):
            query = client.table(table).select(columns)

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.range(offset, offset + limit - 1 if limit else offset + 999)

            return query.execute()

        return await self.execute_with_retry(operation, f"SELECT from {table}")

    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform an INSERT operation with retry logic."""

        def operation(client: Client):
            return client.table(table).insert(data).execute()

        return await self.execute_with_retry(operation, f"INSERT into {table}")

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform an UPDATE operation with retry logic."""

        def operation(client: Client):
            query = client.table(table).update(data)
            for key, value in filters.items():
                query = query.eq(key, value)
            return query.execute()

        return await self.execute_with_retry(operation, f"UPDATE {table}")

    async def delete(self, table: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a DELETE operation with retry logic."""

        def operation(client: Client):
            query = client.table(table).delete()
            for key, value in filters.items():
                query = query.eq(key, value)
            return query.execute()

        return await self.execute_with_retry(operation, f"DELETE from {table}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform a database health check."""
        try:
            start_time = time.time()

            # Simple health check query
            result = await self.select("archon_projects", columns="id", limit=1)

            response_time = time.time() - start_time

            # Update health check stats
            self.connection_pool._stats.last_health_check = time.time()
            self.connection_pool._stats.health_check_failures = 0

            return {
                "status": "healthy",
                "response_time": response_time,
                "pool_stats": self.connection_pool.get_stats().__dict__
            }

        except Exception as e:
            # Update failure stats
            self.connection_pool._stats.health_check_failures += 1

            return {
                "status": "unhealthy",
                "error": str(e),
                "pool_stats": self.connection_pool.get_stats().__dict__
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive client statistics."""
        pool_stats = self.connection_pool.get_stats()

        return {
            "pool": pool_stats.__dict__,
            "config": {
                "max_pool_size": self.config.max_pool_size,
                "retry_attempts": self.config.retry_attempts,
                "connection_timeout": self.config.connection_timeout,
            },
            "uptime": time.time() - getattr(pool_stats, 'last_health_check', time.time())
        }

    async def close(self):
        """Close all connections and cleanup resources."""
        await self.connection_pool.close_all()
        self.logger.info("Enhanced Supabase client closed")


# Global enhanced client instance
_enhanced_client: Optional[EnhancedSupabaseClient] = None

def get_enhanced_supabase_client() -> EnhancedSupabaseClient:
    """Get the global enhanced Supabase client instance."""
    global _enhanced_client

    if _enhanced_client is None:
        _enhanced_client = EnhancedSupabaseClient()

    return _enhanced_client

# Backward compatibility - keep the old function
def get_supabase_client() -> Client:
    """Get a basic Supabase client for backward compatibility."""
    import warnings
    warnings.warn(
        "get_supabase_client() is deprecated. Use get_enhanced_supabase_client() for improved reliability.",
        DeprecationWarning,
        stacklevel=2
    )

    # Create a basic client without pooling
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    return create_client(url, key)
