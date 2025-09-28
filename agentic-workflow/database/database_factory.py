"""
Database Factory for Zippy-Archon

This module provides a unified interface for multiple database backends:
- PostgreSQL (recommended for production)
- SQLite (lightweight for development)
- Supabase (cloud option)
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Unified database configuration."""
    type: str  # 'postgresql', 'sqlite', 'supabase'
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    schema: str = "public"
    timeout: int = 30

class DatabaseManager(Protocol):
    """Protocol for database managers."""

    async def test_connection(self) -> bool:
        """Test database connection."""
        ...

    async def create_requirement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement."""
        ...

    async def get_requirement(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get a requirement by ID."""
        ...

    async def list_requirements(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List requirements."""
        ...

    async def create_ab_test(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create A/B test result."""
        ...

    async def get_ab_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test by ID."""
        ...

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        ...

class PostgreSQLManager:
    """PostgreSQL database manager using asyncpg."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None

    async def initialize(self):
        """Initialize PostgreSQL connection pool."""
        try:
            import asyncpg

            # Build connection string
            if self.config.url:
                self.connection_string = self.config.url
            else:
                self.connection_string = (
                    f"postgresql://{self.config.username}:{self.config.password}"
                    f"@{self.config.host}:{self.config.port}/{self.config.database}"
                )

            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=self.config.timeout
            )

            logger.info("✅ PostgreSQL connection pool initialized")
            return True

        except ImportError:
            logger.error("❌ asyncpg not installed. Install with: pip install asyncpg")
            return False
        except Exception as e:
            logger.error(f"❌ PostgreSQL initialization failed: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def create_requirement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement."""
        try:
            async with self.pool.acquire() as conn:
                # Create table if it doesn't exist
                await self._ensure_requirements_table(conn)

                # Insert requirement
                query = """
                INSERT INTO requirements (
                    id, user_id, prompt, provider, version,
                    requirements_content, design_content, tasks_content,
                    metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                """

                requirement_id = str(uuid.uuid4())
                result = await conn.fetchrow(query,
                    requirement_id,
                    data.get('user_id', 'system'),
                    data.get('prompt', ''),
                    data.get('provider', 'unknown'),
                    data.get('version', 'v1'),
                    data.get('requirements_content', '{}'),
                    data.get('design_content', '{}'),
                    data.get('tasks_content', '{}'),
                    json.dumps(data.get('metadata', {})),
                    datetime.now(),
                    datetime.now()
                )

                if result:
                    data['id'] = requirement_id
                    logger.info(f"Created requirement: {requirement_id}")
                    return data
                else:
                    raise Exception("Failed to create requirement")

        except Exception as e:
            logger.error(f"Failed to create requirement: {e}")
            raise

    async def _ensure_requirements_table(self, conn):
        """Ensure requirements table exists."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS requirements (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            prompt TEXT,
            provider TEXT,
            version TEXT,
            requirements_content TEXT,
            design_content TEXT,
            tasks_content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await conn.execute(create_table_query)

    async def get_requirement(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get a requirement by ID."""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT * FROM requirements WHERE id = $1"
                result = await conn.fetchrow(query, requirement_id)

                if result:
                    return dict(result)
                return None

        except Exception as e:
            logger.error(f"Failed to get requirement {requirement_id}: {e}")
            return None

    async def list_requirements(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List requirements."""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT * FROM requirements ORDER BY created_at DESC LIMIT $1"
                results = await conn.fetch(query, limit)
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to list requirements: {e}")
            return []

    async def create_ab_test(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create A/B test result."""
        try:
            async with self.pool.acquire() as conn:
                await self._ensure_ab_tests_table(conn)

                query = """
                INSERT INTO ab_tests (
                    id, user_id, prompt, versions, results,
                    winner, comparison_metrics, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """

                test_id = str(uuid.uuid4())
                result = await conn.fetchrow(query,
                    test_id,
                    data.get('user_id', 'system'),
                    data.get('prompt', ''),
                    json.dumps(data.get('versions', [])),
                    json.dumps(data.get('results', {})),
                    data.get('winner', ''),
                    json.dumps(data.get('comparison_metrics', {})),
                    datetime.now(),
                    datetime.now()
                )

                if result:
                    data['id'] = test_id
                    logger.info(f"Created A/B test: {test_id}")
                    return data
                else:
                    raise Exception("Failed to create A/B test")

        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            raise

    async def _ensure_ab_tests_table(self, conn):
        """Ensure ab_tests table exists."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS ab_tests (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            prompt TEXT,
            versions TEXT,
            results TEXT,
            winner TEXT,
            comparison_metrics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await conn.execute(create_table_query)

    async def get_ab_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test by ID."""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT * FROM ab_tests WHERE id = $1"
                result = await conn.fetchrow(query, test_id)

                if result:
                    return dict(result)
                return None

        except Exception as e:
            logger.error(f"Failed to get A/B test {test_id}: {e}")
            return None

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        try:
            async with self.pool.acquire() as conn:
                # Count requirements
                req_count = await conn.fetchval("SELECT COUNT(*) FROM requirements")
                # Count A/B tests
                ab_count = await conn.fetchval("SELECT COUNT(*) FROM ab_tests")

                return {
                    "total_requirements": req_count or 0,
                    "total_ab_tests": ab_count or 0,
                    "total_listings": 0,  # Placeholder
                    "total_users": 1,     # Placeholder
                    "total_volume": 0,    # Placeholder
                    "generated_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get platform stats: {e}")
            return {
                "total_requirements": 0,
                "total_ab_tests": 0,
                "total_listings": 0,
                "total_users": 0,
                "total_volume": 0,
                "generated_at": datetime.now().isoformat()
            }

class SQLiteManager:
    """SQLite database manager for lightweight development."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = config.database or "zippy_archon.db"

    async def initialize(self):
        """Initialize SQLite database."""
        try:
            import aiosqlite
            import sqlite3

            # Create database file if it doesn't exist
            if not os.path.exists(self.db_path):
                # Create tables synchronously first
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Create requirements table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS requirements (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    prompt TEXT,
                    provider TEXT,
                    version TEXT,
                    requirements_content TEXT,
                    design_content TEXT,
                    tasks_content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Create ab_tests table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS ab_tests (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    prompt TEXT,
                    versions TEXT,
                    results TEXT,
                    winner TEXT,
                    comparison_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                conn.commit()
                conn.close()

            logger.info(f"✅ SQLite database initialized: {self.db_path}")
            return True

        except ImportError:
            logger.error("❌ aiosqlite not installed. Install with: pip install aiosqlite")
            return False
        except Exception as e:
            logger.error(f"❌ SQLite initialization failed: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            import aiosqlite
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT 1") as cursor:
                    result = await cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def create_requirement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                requirement_id = str(uuid.uuid4())

                await db.execute('''
                INSERT INTO requirements (
                    id, user_id, prompt, provider, version,
                    requirements_content, design_content, tasks_content,
                    metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    requirement_id,
                    data.get('user_id', 'system'),
                    data.get('prompt', ''),
                    data.get('provider', 'unknown'),
                    data.get('version', 'v1'),
                    data.get('requirements_content', '{}'),
                    data.get('design_content', '{}'),
                    data.get('tasks_content', '{}'),
                    json.dumps(data.get('metadata', {})),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

                await db.commit()
                data['id'] = requirement_id
                logger.info(f"Created requirement: {requirement_id}")
                return data

        except Exception as e:
            logger.error(f"Failed to create requirement: {e}")
            raise

    async def get_requirement(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get a requirement by ID."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, row))
                    return None

        except Exception as e:
            logger.error(f"Failed to get requirement {requirement_id}: {e}")
            return None

    async def list_requirements(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List requirements."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT * FROM requirements ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        return [dict(zip(columns, row)) for row in rows]
                    return []

        except Exception as e:
            logger.error(f"Failed to list requirements: {e}")
            return []

    async def create_ab_test(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create A/B test result."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                test_id = str(uuid.uuid4())

                await db.execute('''
                INSERT INTO ab_tests (
                    id, user_id, prompt, versions, results,
                    winner, comparison_metrics, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    data.get('user_id', 'system'),
                    data.get('prompt', ''),
                    json.dumps(data.get('versions', [])),
                    json.dumps(data.get('results', {})),
                    data.get('winner', ''),
                    json.dumps(data.get('comparison_metrics', {})),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

                await db.commit()
                data['id'] = test_id
                logger.info(f"Created A/B test: {test_id}")
                return data

        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            raise

    async def get_ab_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test by ID."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT * FROM ab_tests WHERE id = ?", (test_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, row))
                    return None

        except Exception as e:
            logger.error(f"Failed to get A/B test {test_id}: {e}")
            return None

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                # Count requirements
                async with db.execute("SELECT COUNT(*) FROM requirements") as cursor:
                    req_count = (await cursor.fetchone())[0]

                # Count A/B tests
                async with db.execute("SELECT COUNT(*) FROM ab_tests") as cursor:
                    ab_count = (await cursor.fetchone())[0]

                return {
                    "total_requirements": req_count,
                    "total_ab_tests": ab_count,
                    "total_listings": 0,  # Placeholder
                    "total_users": 1,     # Placeholder
                    "total_volume": 0,    # Placeholder
                    "generated_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get platform stats: {e}")
            return {
                "total_requirements": 0,
                "total_ab_tests": 0,
                "total_listings": 0,
                "total_users": 0,
                "total_volume": 0,
                "generated_at": datetime.now().isoformat()
            }

class DatabaseFactory:
    """Factory for creating database managers."""

    @staticmethod
    def create_database(config: DatabaseConfig) -> DatabaseManager:
        """Create database manager based on configuration."""
        if config.type.lower() == 'postgresql':
            return PostgreSQLManager(config)
        elif config.type.lower() == 'sqlite':
            return SQLiteManager(config)
        elif config.type.lower() == 'supabase':
            # Import here to avoid circular dependency
            from .supabase_client import SupabaseManager
            return SupabaseManager(config)
        else:
            raise ValueError(f"Unsupported database type: {config.type}")

    @staticmethod
    def create_config_from_env() -> DatabaseConfig:
        """Create database configuration from environment variables."""
        db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()

        if db_type == 'postgresql':
            return DatabaseConfig(
                type='postgresql',
                host=os.getenv('DATABASE_HOST', 'localhost'),
                port=int(os.getenv('DATABASE_PORT', '5432')),
                database=os.getenv('DATABASE_NAME', 'zippy_archon'),
                username=os.getenv('DATABASE_USER', 'zippy'),
                password=os.getenv('DATABASE_PASSWORD', 'password'),
                schema=os.getenv('DATABASE_SCHEMA', 'public')
            )
        elif db_type == 'sqlite':
            return DatabaseConfig(
                type='sqlite',
                database=os.getenv('DATABASE_PATH', 'zippy_archon.db')
            )
        elif db_type == 'supabase':
            return DatabaseConfig(
                type='supabase',
                url=os.getenv('SUPABASE_URL'),
                api_key=os.getenv('SUPABASE_SERVICE_KEY'),
                schema=os.getenv('SUPABASE_SCHEMA', 'public')
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

async def initialize_database() -> DatabaseManager:
    """Initialize database connection."""
    global db_manager

    if db_manager is not None:
        return db_manager

    try:
        config = DatabaseFactory.create_config_from_env()
        db_manager = DatabaseFactory.create_database(config)

        # Initialize the database (create tables, etc.)
        if hasattr(db_manager, 'initialize'):
            success = await db_manager.initialize()
            if not success:
                raise Exception("Database initialization failed")

        # Test connection
        if not await db_manager.test_connection():
            raise Exception("Database connection test failed")

        logger.info(f"✅ Database initialized successfully: {config.type}")
        return db_manager

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def get_database_manager() -> Optional[DatabaseManager]:
    """Get the global database manager instance."""
    return db_manager
