"""
Tests for database services including Supabase client, credential service, and data operations
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

# Mock the database client before importing services
with patch('python.src.server.services.supabase_client.create_client'):
    from python.src.server.services.credential_service import CredentialService
    from python.src.server.services.supabase_client import SupabaseClient
    from python.src.server.services.projects import ProjectService, TaskService
    from python.src.server.services.knowledge import KnowledgeService

class TestSupabaseClient:
    """Test suite for Supabase client operations."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        return mock_client, mock_table

    def test_connection_initialization(self, mock_supabase):
        """Test Supabase client initialization."""
        mock_client, _ = mock_supabase

        with patch('python.src.server.services.supabase_client.create_client', return_value=mock_client):
            client = SupabaseClient()
            assert client.client is not None

    def test_query_execution(self, mock_supabase):
        """Test basic query execution."""
        mock_client, mock_table = mock_supabase

        # Mock the query chain
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = {"data": [{"id": 1, "name": "test"}]}

        with patch('python.src.server.services.supabase_client.create_client', return_value=mock_client):
            client = SupabaseClient()
            result = client.select("test_table", columns=["id", "name"], filters={"status": "active"})

            assert result["data"][0]["name"] == "test"
            mock_table.select.assert_called_with("id,name")
            mock_query.eq.assert_called_with("status", "active")

    def test_insert_operation(self, mock_supabase):
        """Test insert operations."""
        mock_client, mock_table = mock_supabase

        mock_table.insert.return_value.execute.return_value = {"data": [{"id": 1}]}

        with patch('python.src.server.services.supabase_client.create_client', return_value=mock_client):
            client = SupabaseClient()
            data = {"name": "test", "value": 123}
            result = client.insert("test_table", data)

            assert result["data"][0]["id"] == 1
            mock_table.insert.assert_called_with(data)

    def test_update_operation(self, mock_supabase):
        """Test update operations."""
        mock_client, mock_table = mock_supabase

        mock_query = MagicMock()
        mock_table.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = {"data": [{"id": 1, "updated": True}]}

        with patch('python.src.server.services.supabase_client.create_client', return_value=mock_client):
            client = SupabaseClient()
            updates = {"status": "updated"}
            result = client.update("test_table", updates, {"id": 1})

            assert result["data"][0]["updated"] is True

    def test_delete_operation(self, mock_supabase):
        """Test delete operations."""
        mock_client, mock_table = mock_supabase

        mock_query = MagicMock()
        mock_table.delete.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = {"data": None}

        with patch('python.src.server.services.supabase_client.create_client', return_value=mock_client):
            client = SupabaseClient()
            result = client.delete("test_table", {"id": 1})

            assert result["data"] is None

    def test_error_handling(self, mock_supabase):
        """Test error handling for failed operations."""
        mock_client, mock_table = mock_supabase

        mock_table.select.side_effect = Exception("Database connection failed")

        with patch('python.src.server.services.supabase_client.create_client', return_value=mock_client):
            client = SupabaseClient()

            with pytest.raises(Exception, match="Database connection failed"):
                client.select("test_table")

class TestCredentialService:
    """Test suite for credential management."""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for credential service."""
        mock_client = MagicMock()
        return mock_client

    def test_get_credentials_by_category(self, mock_supabase_client):
        """Test retrieving credentials by category."""
        with patch('python.src.server.services.credential_service.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.select.return_value = {
                "data": [
                    {
                        "id": "1",
                        "category": "api_keys",
                        "name": "OpenAI Key",
                        "value": "sk-1234567890abcdef",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }

            service = CredentialService()
            credentials = service.get_credentials_by_category("api_keys")

            assert len(credentials) == 1
            assert credentials[0]["name"] == "OpenAI Key"

    def test_set_credentials(self, mock_supabase_client):
        """Test setting new credentials."""
        with patch('python.src.server.services.credential_service.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.insert.return_value = {"data": [{"id": "new-id"}]}

            service = CredentialService()
            result = service.set_credentials({
                "category": "api_keys",
                "name": "Test Key",
                "value": "test-value"
            })

            assert result["data"][0]["id"] == "new-id"

    def test_update_credentials(self, mock_supabase_client):
        """Test updating existing credentials."""
        with patch('python.src.server.services.credential_service.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.update.return_value = {"data": [{"id": "1", "updated": True}]}

            service = CredentialService()
            result = service.update_credentials("1", {"value": "new-value"})

            assert result["data"][0]["updated"] is True

    def test_delete_credentials(self, mock_supabase_client):
        """Test deleting credentials."""
        with patch('python.src.server.services.credential_service.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.delete.return_value = {"data": None}

            service = CredentialService()
            result = service.delete_credentials("1")

            assert result["data"] is None

    def test_credential_validation(self, mock_supabase_client):
        """Test credential validation."""
        with patch('python.src.server.services.credential_service.get_supabase_client', return_value=mock_supabase_client):
            service = CredentialService()

            # Test valid API key format
            assert service.validate_api_key("sk-1234567890abcdef", "openai")

            # Test invalid API key format
            assert not service.validate_api_key("invalid-key", "openai")

    def test_encryption_operations(self, mock_supabase_client):
        """Test credential encryption/decryption."""
        with patch('python.src.server.services.credential_service.get_supabase_client', return_value=mock_supabase_client):
            service = CredentialService()

            test_value = "sensitive-api-key"
            encrypted = service.encrypt_value(test_value)
            decrypted = service.decrypt_value(encrypted)

            assert decrypted == test_value
            assert encrypted != test_value  # Ensure encryption actually happened

class TestProjectService:
    """Test suite for project management operations."""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for project service."""
        mock_client = MagicMock()
        return mock_client

    def test_create_project(self, mock_supabase_client):
        """Test project creation."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.insert.return_value = {
                "data": [{
                    "id": "project-123",
                    "title": "Test Project",
                    "description": "A test project",
                    "created_at": "2024-01-01T00:00:00Z"
                }]
            }

            service = ProjectService()
            project_data = {
                "title": "Test Project",
                "description": "A test project",
                "github_repo": "https://github.com/test/repo"
            }

            result = service.create_project(project_data)

            assert result["data"][0]["id"] == "project-123"
            assert result["data"][0]["title"] == "Test Project"

    def test_get_project(self, mock_supabase_client):
        """Test retrieving a specific project."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.select.return_value = {
                "data": [{
                    "id": "project-123",
                    "title": "Test Project",
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00Z"
                }]
            }

            service = ProjectService()
            result = service.get_project("project-123")

            assert result["data"][0]["id"] == "project-123"

    def test_list_projects(self, mock_supabase_client):
        """Test listing all projects."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.select.return_value = {
                "data": [
                    {
                        "id": "project-1",
                        "title": "Project 1",
                        "status": "active"
                    },
                    {
                        "id": "project-2",
                        "title": "Project 2",
                        "status": "completed"
                    }
                ]
            }

            service = ProjectService()
            result = service.list_projects()

            assert len(result["data"]) == 2
            assert result["data"][0]["title"] == "Project 1"

    def test_update_project(self, mock_supabase_client):
        """Test project updates."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.update.return_value = {
                "data": [{
                    "id": "project-123",
                    "title": "Updated Project",
                    "updated_at": "2024-01-02T00:00:00Z"
                }]
            }

            service = ProjectService()
            updates = {"title": "Updated Project"}
            result = service.update_project("project-123", updates)

            assert result["data"][0]["title"] == "Updated Project"

    def test_delete_project(self, mock_supabase_client):
        """Test project deletion."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.delete.return_value = {"data": None}

            service = ProjectService()
            result = service.delete_project("project-123")

            assert result["data"] is None

    def test_project_validation(self, mock_supabase_client):
        """Test project data validation."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            service = ProjectService()

            # Test valid project data
            valid_data = {
                "title": "Valid Project",
                "description": "A valid project description"
            }
            assert service.validate_project_data(valid_data)

            # Test invalid project data (missing title)
            invalid_data = {"description": "Missing title"}
            assert not service.validate_project_data(invalid_data)

class TestTaskService:
    """Test suite for task management operations."""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for task service."""
        mock_client = MagicMock()
        return mock_client

    def test_create_task(self, mock_supabase_client):
        """Test task creation."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.insert.return_value = {
                "data": [{
                    "id": "task-123",
                    "title": "Test Task",
                    "status": "todo",
                    "project_id": "project-123"
                }]
            }

            service = TaskService()
            task_data = {
                "project_id": "project-123",
                "title": "Test Task",
                "description": "A test task",
                "status": "todo"
            }

            result = service.create_task(task_data)

            assert result["data"][0]["id"] == "task-123"
            assert result["data"][0]["status"] == "todo"

    def test_get_tasks_by_project(self, mock_supabase_client):
        """Test retrieving tasks for a project."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.select.return_value = {
                "data": [
                    {
                        "id": "task-1",
                        "title": "Task 1",
                        "status": "todo",
                        "project_id": "project-123"
                    },
                    {
                        "id": "task-2",
                        "title": "Task 2",
                        "status": "in_progress",
                        "project_id": "project-123"
                    }
                ]
            }

            service = TaskService()
            result = service.get_tasks_by_project("project-123")

            assert len(result["data"]) == 2
            assert all(task["project_id"] == "project-123" for task in result["data"])

    def test_update_task_status(self, mock_supabase_client):
        """Test updating task status."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.update.return_value = {
                "data": [{
                    "id": "task-123",
                    "status": "completed",
                    "updated_at": "2024-01-02T00:00:00Z"
                }]
            }

            service = TaskService()
            result = service.update_task_status("task-123", "completed")

            assert result["data"][0]["status"] == "completed"

    def test_task_reordering(self, mock_supabase_client):
        """Test task reordering functionality."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.update.return_value = {"data": [{"id": "task-123", "task_order": 2}]}

            service = TaskService()
            result = service.reorder_task("task-123", 2)

            assert result["data"][0]["task_order"] == 2

    def test_bulk_task_operations(self, mock_supabase_client):
        """Test bulk task operations."""
        with patch('python.src.server.services.projects.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.update.return_value = {
                "data": [
                    {"id": "task-1", "status": "completed"},
                    {"id": "task-2", "status": "completed"}
                ]
            }

            service = TaskService()
            task_ids = ["task-1", "task-2"]
            result = service.bulk_update_status(task_ids, "completed")

            assert len(result["data"]) == 2
            assert all(task["status"] == "completed" for task in result["data"])

class TestKnowledgeService:
    """Test suite for knowledge management operations."""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for knowledge service."""
        mock_client = MagicMock()
        return mock_client

    def test_add_knowledge_item(self, mock_supabase_client):
        """Test adding knowledge items."""
        with patch('python.src.server.services.knowledge.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.insert.return_value = {
                "data": [{
                    "id": "knowledge-123",
                    "title": "Test Document",
                    "content": "Test content",
                    "source_url": "https://example.com"
                }]
            }

            service = KnowledgeService()
            knowledge_data = {
                "title": "Test Document",
                "content": "Test content",
                "source_url": "https://example.com",
                "content_type": "document"
            }

            result = service.add_knowledge_item(knowledge_data)

            assert result["data"][0]["id"] == "knowledge-123"
            assert result["data"][0]["title"] == "Test Document"

    def test_search_knowledge(self, mock_supabase_client):
        """Test knowledge search functionality."""
        with patch('python.src.server.services.knowledge.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.select.return_value = {
                "data": [
                    {
                        "id": "knowledge-1",
                        "title": "Python Guide",
                        "content": "Python programming guide",
                        "relevance_score": 0.95
                    }
                ]
            }

            service = KnowledgeService()
            result = service.search_knowledge("python programming", limit=10)

            assert len(result["data"]) == 1
            assert result["data"][0]["title"] == "Python Guide"

    def test_get_knowledge_item(self, mock_supabase_client):
        """Test retrieving specific knowledge items."""
        with patch('python.src.server.services.knowledge.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.select.return_value = {
                "data": [{
                    "id": "knowledge-123",
                    "title": "Test Document",
                    "content": "Full content here",
                    "metadata": {"word_count": 100}
                }]
            }

            service = KnowledgeService()
            result = service.get_knowledge_item("knowledge-123")

            assert result["data"][0]["id"] == "knowledge-123"
            assert result["data"][0]["content"] == "Full content here"

    def test_update_knowledge_item(self, mock_supabase_client):
        """Test updating knowledge items."""
        with patch('python.src.server.services.knowledge.get_supabase_client', return_value=mock_supabase_client):
            mock_supabase_client.update.return_value = {
                "data": [{
                    "id": "knowledge-123",
                    "title": "Updated Title",
                    "updated_at": "2024-01-02T00:00:00Z"
                }]
            }

            service = KnowledgeService()
            updates = {"title": "Updated Title"}
            result = service.update_knowledge_item("knowledge-123", updates)

            assert result["data"][0]["title"] == "Updated Title"

    def test_categorize_knowledge(self, mock_supabase_client):
        """Test knowledge categorization."""
        with patch('python.src.server.services.knowledge.get_supabase_client', return_value=mock_supabase_client):
            service = KnowledgeService()

            content = "This is a Python tutorial about functions and classes."
            category = service.categorize_content(content)

            assert category in ["tutorial", "documentation", "code", "general"]

    def test_knowledge_validation(self, mock_supabase_client):
        """Test knowledge item validation."""
        with patch('python.src.server.services.knowledge.get_supabase_client', return_value=mock_supabase_client):
            service = KnowledgeService()

            # Test valid knowledge data
            valid_data = {
                "title": "Valid Document",
                "content": "Valid content",
                "content_type": "document"
            }
            assert service.validate_knowledge_data(valid_data)

            # Test invalid knowledge data
            invalid_data = {"title": ""}  # Empty title
            assert not service.validate_knowledge_data(invalid_data)
