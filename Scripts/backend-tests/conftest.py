"""
Pytest configuration and fixtures for Zippy Archon backend testing
"""

import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agentic-workflow'))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from httpx import AsyncClient

# Mock environment variables for testing
os.environ.update({
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_SERVICE_KEY': 'test-service-key',
    'OPENAI_API_KEY': 'test-openai-key',
    'ANTHROPIC_API_KEY': 'test-anthropic-key',
    'GROK_API_KEY': 'test-grok-key',
    'REDIS_URL': 'redis://localhost:6379/1',
    'ENVIRONMENT': 'test',
    'SENTRY_DSN': '',
    'RELEASE_VERSION': 'test-1.0.0'
})

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = AsyncMock()
    mock_client.table.return_value = AsyncMock()
    mock_client.rpc.return_value = AsyncMock()
    return mock_client

@pytest.fixture
async def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.models.list = AsyncMock()
    return mock_client

@pytest.fixture
async def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.set = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.exists = AsyncMock()
    return mock_client

@pytest.fixture
def mock_trust_manager():
    """Mock ZippyTrust manager for testing."""
    mock_manager = MagicMock()
    mock_manager.verify_plugin = AsyncMock()
    mock_manager.get_trust_score = AsyncMock()
    mock_manager.update_trust_score = AsyncMock()
    return mock_manager

@pytest.fixture
def mock_marketplace():
    """Mock ZippyCoin marketplace for testing."""
    mock_marketplace = MagicMock()
    mock_marketplace.create_listing = AsyncMock()
    mock_marketplace.purchase_listing = AsyncMock()
    mock_marketplace.get_listing = AsyncMock()
    return mock_marketplace

@pytest.fixture
def mock_ab_testing():
    """Mock A/B testing system for testing."""
    mock_testing = MagicMock()
    mock_testing.run_prompt_comparison = AsyncMock()
    mock_testing.get_test_results = AsyncMock()
    return mock_testing

@pytest.fixture
def mock_rubric_scorer():
    """Mock rubric scorer for testing."""
    mock_scorer = MagicMock()
    mock_scorer.score_content = AsyncMock()
    mock_scorer.get_enhanced_score = AsyncMock()
    return mock_scorer

@pytest.fixture
async def test_app() -> FastAPI:
    """Create a test FastAPI application."""
    from api.fastapi_server import app
    return app

@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncClient:
    """Create an async test client."""
    client = AsyncClient(app=test_app, base_url="http://test")
    yield client
    await client.aclose()

@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Create a synchronous test client."""
    return TestClient(test_app)

@pytest.fixture
def sample_requirement_data() -> Dict[str, Any]:
    """Sample requirement data for testing."""
    return {
        "title": "Test Requirement",
        "description": "A test requirement for testing purposes",
        "priority": "high",
        "status": "draft",
        "tags": ["test", "requirement"],
        "author": "test-user",
        "version": "1.0.0"
    }

@pytest.fixture
def sample_ab_test_data() -> Dict[str, Any]:
    """Sample A/B test data for testing."""
    return {
        "prompt": "Test feature description",
        "versions": ["v1", "v1b", "enhanced"],
        "provider": "grok",
        "rubric_weights": {
            "clarity": 0.25,
            "structure": 0.25,
            "testability": 0.25,
            "conformity": 0.25
        },
        "trust_threshold": 0.7,
        "marketplace_publish": True
    }

@pytest.fixture
def sample_plugin_data() -> Dict[str, Any]:
    """Sample plugin data for testing."""
    return {
        "name": "test_plugin",
        "description": "A test plugin for testing purposes",
        "author": "test-author",
        "version": "1.0.0",
        "dependencies": [],
        "tags": ["test", "plugin"],
        "license": "MIT"
    }

@pytest.fixture
async def mock_database_manager():
    """Mock database manager for testing."""
    mock_manager = AsyncMock()
    mock_manager.create_requirement = AsyncMock()
    mock_manager.get_requirement = AsyncMock()
    mock_manager.list_requirements = AsyncMock()
    mock_manager.create_ab_test = AsyncMock()
    mock_manager.get_ab_test = AsyncMock()
    mock_manager.get_platform_stats = AsyncMock()
    return mock_manager

@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing."""
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock()
    mock_provider.is_available = AsyncMock(return_value=True)
    return mock_provider

@pytest.fixture
def plugins_directory():
    """Provide plugins directory path for tests."""
    import os
    # Use absolute path to avoid relative path issues
    current_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(current_dir, '..', '..', 'agentic-workflow', 'plugins')
    return plugins_dir

@pytest.fixture
def mock_plugin_manager():
    """Mock plugin manager for testing."""
    mock_manager = MagicMock()
    mock_manager.register_tool = MagicMock()
    mock_manager.load_plugins = MagicMock()
    mock_manager.get_tool_by_name = MagicMock()
    return mock_manager

# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_requirement(**kwargs) -> Dict[str, Any]:
        """Create a test requirement."""
        default_data = {
            "id": "test-req-123",
            "title": "Test Requirement",
            "description": "A test requirement",
            "priority": "medium",
            "status": "draft",
            "tags": ["test"],
            "author": "test-user",
            "version": "1.0.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_ab_test(**kwargs) -> Dict[str, Any]:
        """Create a test A/B test."""
        default_data = {
            "id": "test-ab-123",
            "prompt": "Test prompt",
            "versions": ["v1", "v2"],
            "winner": "v1",
            "winner_score": 0.85,
            "trust_scores": {"v1": 0.8, "v2": 0.7},
            "created_at": "2024-01-01T00:00:00Z"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_plugin(**kwargs) -> Dict[str, Any]:
        """Create a test plugin."""
        default_data = {
            "id": "test-plugin-123",
            "name": "test_plugin",
            "description": "Test plugin",
            "author": "test-author",
            "version": "1.0.0",
            "trust_score": 0.8,
            "verification_status": "verified"
        }
        default_data.update(kwargs)
        return default_data

@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory
