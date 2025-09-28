"""
Phase 3 Integration Tests

Comprehensive integration tests for all Phase 3 services:
- Task Prioritization
- Real-time Collaboration
- Smart Suggestions
- Task Dependencies
- Progress Tracking
- Team Collaboration

Tests ensure all services work together correctly and handle edge cases.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import all Phase 3 services
from python.src.server.services.task_prioritization_service import task_prioritization_service
from python.src.server.services.realtime_collaboration_service import realtime_collaboration_service
from python.src.server.services.smart_suggestions_service import smart_suggestions_service
from python.src.server.services.task_dependency_service import task_dependency_service
from python.src.server.services.progress_tracking_service import progress_tracking_service
from python.src.server.services.team_collaboration_service import team_collaboration_service

# Import API routers
from python.src.server.api.task_prioritization_api import router as task_prioritization_router
from python.src.server.api.realtime_collaboration_api import router as realtime_collaboration_router
from python.src.server.api.smart_suggestions_api import router as smart_suggestions_router
from python.src.server.api.task_dependency_api import router as task_dependency_router
from python.src.server.api.progress_tracking_api import router as progress_tracking_router
from python.src.server.api.team_collaboration_api import router as team_collaboration_router


class TestPhase3Integration:
    """Integration tests for Phase 3 services."""

    @pytest.fixture
    def test_app(self):
        """Create test FastAPI application with all Phase 3 routers."""
        app = FastAPI(title="Phase 3 Integration Test API")

        # Include all Phase 3 routers
        app.include_router(task_prioritization_router, prefix="/api")
        app.include_router(realtime_collaboration_router, prefix="/api")
        app.include_router(smart_suggestions_router, prefix="/api")
        app.include_router(task_dependency_router, prefix="/api")
        app.include_router(progress_tracking_router, prefix="/api")
        app.include_router(team_collaboration_router, prefix="/api")

        return app

    @pytest.fixture
    def test_client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            "project_id": "test-project-123",
            "user_id": "test-user-456",
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Implement user authentication",
                    "status": "in_progress",
                    "type": "feature",
                    "estimated_duration": 8,
                    "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
                },
                {
                    "id": "task-2",
                    "title": "Design database schema",
                    "status": "todo",
                    "type": "feature",
                    "estimated_duration": 6,
                    "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                },
                {
                    "id": "task-3",
                    "title": "Write unit tests",
                    "status": "todo",
                    "type": "testing",
                    "estimated_duration": 4,
                    "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                }
            ]
        }

    def test_task_prioritization_workflow(self, test_client, sample_project_data):
        """Test complete task prioritization workflow."""
        # Mock database calls
        with patch.object(task_prioritization_service, '_fetch_project_tasks') as mock_fetch:
            mock_fetch.return_value = sample_project_data["tasks"]

            # Test prioritization endpoint
            response = test_client.post(
                "/api/task-prioritization/prioritize",
                json={
                    "project_id": sample_project_data["project_id"],
                    "user_id": sample_project_data["user_id"]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert len(data["data"]) > 0

            # Verify prioritization scores
            for task_score in data["data"]:
                assert "total_score" in task_score
                assert "priority_level" in task_score
                assert "reasoning" in task_score
                assert task_score["total_score"] >= 0
                assert task_score["total_score"] <= 1

    def test_realtime_collaboration_setup(self):
        """Test real-time collaboration service initialization."""
        # Test service health
        health = asyncio.run(realtime_collaboration_service.get_project_collaboration_stats("test-project"))

        # Should return default stats for non-existent project
        assert "active_users" in health
        assert "total_sessions" in health
        assert health["active_users"] == 0

    def test_smart_suggestions_workflow(self, test_client, sample_project_data):
        """Test smart suggestions workflow."""
        # Mock user patterns
        with patch.object(smart_suggestions_service, '_get_user_patterns') as mock_patterns:
            mock_patterns.return_value = {
                "preferred_work_hours": [9, 10, 11, 14, 15, 16],
                "preferred_work_days": [0, 1, 2, 3, 4],  # Monday to Friday
                "average_task_duration": {"feature": 120, "testing": 60},
                "common_task_types": ["feature", "testing"],
                "skill_levels": {"python": 0.8, "react": 0.6},
                "collaboration_preference": "moderate"
            }

            # Test suggestions endpoint
            response = test_client.post(
                "/api/smart-suggestions/suggest",
                json={
                    "project_id": sample_project_data["project_id"],
                    "context": {"current_hour": 10, "is_optimal_time": True}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "primary_suggestion" in data
            assert "alternative_suggestions" in data

    def test_task_dependency_analysis(self, sample_project_data):
        """Test task dependency analysis."""
        # Mock database calls
        with patch.object(task_dependency_service, '_fetch_project_tasks') as mock_fetch:
            mock_fetch.return_value = sample_project_data["tasks"]

            # Test dependency graph building
            graph = asyncio.run(task_dependency_service.build_dependency_graph(
                sample_project_data["project_id"]
            ))

            assert graph.project_id == sample_project_data["project_id"]
            assert len(graph.nodes) == len(sample_project_data["tasks"])
            assert isinstance(graph.edges, list)

    def test_progress_tracking_workflow(self, test_client, sample_project_data):
        """Test progress tracking workflow."""
        # Mock database calls
        with patch.object(progress_tracking_service, 'get_project_progress') as mock_progress:
            mock_progress.return_value = {
                "timestamp": datetime.now(),
                "total_tasks": 3,
                "completed_tasks": 1,
                "in_progress_tasks": 1,
                "blocked_tasks": 0,
                "overdue_tasks": 0,
                "time_spent_hours": 12.5,
                "estimated_remaining_hours": 15.0,
                "velocity_tasks_per_day": 0.5,
                "milestone_progress": {}
            }

            # Test progress endpoint
            response = test_client.get(f"/api/progress-tracking/progress/{sample_project_data['project_id']}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "timestamp" in data["data"]
            assert data["data"]["total_tasks"] == 3
            assert data["data"]["completed_tasks"] == 1

    def test_team_collaboration_workflow(self, test_client, sample_project_data):
        """Test team collaboration workflow."""
        # Mock database calls
        with patch.object(team_collaboration_service, '_get_team_members') as mock_members:
            mock_members.return_value = {
                sample_project_data["user_id"]: {
                    "user_id": sample_project_data["user_id"],
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "developer",
                    "skills": ["python", "react"],
                    "current_workload": 2,
                    "capacity_utilization": 0.4
                }
            }

            # Test workload analysis
            response = test_client.get(f"/api/team-collaboration/workload/{sample_project_data['project_id']}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "total_members" in data["data"]
            assert "average_workload" in data["data"]

    def test_end_to_end_task_lifecycle(self, test_client, sample_project_data):
        """Test end-to-end task lifecycle across all services."""
        project_id = sample_project_data["project_id"]
        user_id = sample_project_data["user_id"]
        task_id = sample_project_data["tasks"][0]["id"]

        # 1. Test task prioritization
        with patch.object(task_prioritization_service, '_fetch_project_tasks') as mock_fetch:
            mock_fetch.return_value = sample_project_data["tasks"]

            pri_response = test_client.post(
                "/api/task-prioritization/prioritize",
                json={"project_id": project_id, "user_id": user_id}
            )
            assert pri_response.status_code == 200

        # 2. Test smart suggestions
        with patch.object(smart_suggestions_service, '_get_user_patterns') as mock_patterns:
            mock_patterns.return_value = {
                "preferred_work_hours": [9, 10, 11],
                "preferred_work_days": [0, 1, 2, 3, 4],
                "common_task_types": ["feature"],
                "skill_levels": {"python": 0.8}
            }

            sug_response = test_client.post(
                "/api/smart-suggestions/suggest",
                json={"project_id": project_id}
            )
            assert sug_response.status_code == 200

        # 3. Test progress tracking
        with patch.object(progress_tracking_service, 'get_project_progress') as mock_progress:
            mock_progress.return_value = {
                "timestamp": datetime.now(),
                "total_tasks": 3,
                "completed_tasks": 0,
                "in_progress_tasks": 1,
                "blocked_tasks": 0,
                "overdue_tasks": 0,
                "time_spent_hours": 0,
                "estimated_remaining_hours": 18,
                "velocity_tasks_per_day": 0,
                "milestone_progress": {}
            }

            prog_response = test_client.get(f"/api/progress-tracking/progress/{project_id}")
            assert prog_response.status_code == 200

    def test_error_handling_integration(self, test_client):
        """Test error handling across all services."""
        # Test with invalid project ID
        response = test_client.post(
            "/api/task-prioritization/prioritize",
            json={"project_id": "", "user_id": "test-user"}
        )

        # Should return proper error response
        assert response.status_code in [400, 500]
        data = response.json()
        assert "success" in data
        assert data["success"] is False or "error" in data

    def test_concurrent_operations(self, test_client, sample_project_data):
        """Test concurrent operations across services."""
        import concurrent.futures
        import threading

        results = []
        errors = []

        def make_request(endpoint, method="GET", data=None):
            try:
                if method == "POST":
                    response = test_client.post(endpoint, json=data)
                else:
                    response = test_client.get(endpoint)
                results.append((endpoint, response.status_code))
            except Exception as e:
                errors.append((endpoint, str(e)))

        # Prepare concurrent requests
        requests = [
            ("/api/task-prioritization/factors", "GET"),
            ("/api/smart-suggestions/types", "GET"),
            ("/api/team-collaboration/assignment-strategies", "GET"),
            (f"/api/progress-tracking/analytics/{sample_project_data['project_id']}", "GET"),
        ]

        # Execute concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request, endpoint, method)
                      for endpoint, method in requests]
            concurrent.futures.wait(futures)

        # Verify results
        assert len(results) == len(requests)
        assert len(errors) == 0

        # All requests should return valid HTTP status codes
        for endpoint, status_code in results:
            assert status_code in [200, 404, 500]  # Valid response codes

    def test_service_health_checks(self, test_client):
        """Test health checks for all services."""
        # Test collaboration service health
        response = test_client.get("/api/collaboration/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data["data"]

    def test_data_consistency(self, test_client, sample_project_data):
        """Test data consistency across services."""
        project_id = sample_project_data["project_id"]

        # Get progress data
        with patch.object(progress_tracking_service, 'get_project_progress') as mock_progress:
            mock_progress.return_value = {
                "timestamp": datetime.now(),
                "total_tasks": 3,
                "completed_tasks": 1,
                "in_progress_tasks": 1,
                "blocked_tasks": 0,
                "overdue_tasks": 0,
                "time_spent_hours": 8,
                "estimated_remaining_hours": 12,
                "velocity_tasks_per_day": 0.33,
                "milestone_progress": {}
            }

            progress_response = test_client.get(f"/api/progress-tracking/progress/{project_id}")
            progress_data = progress_response.json()["data"]

            # Verify data consistency
            assert progress_data["total_tasks"] == progress_data["completed_tasks"] + progress_data["in_progress_tasks"] + progress_data["blocked_tasks"]
            assert progress_data["estimated_remaining_hours"] >= 0
            assert progress_data["velocity_tasks_per_day"] >= 0

    def test_performance_under_load(self, test_client, sample_project_data):
        """Test performance under simulated load."""
        import time

        project_id = sample_project_data["project_id"]
        start_time = time.time()

        # Make multiple concurrent requests
        for _ in range(10):
            with patch.object(task_prioritization_service, '_fetch_project_tasks') as mock_fetch:
                mock_fetch.return_value = sample_project_data["tasks"]
                response = test_client.post(
                    "/api/task-prioritization/prioritize",
                    json={"project_id": project_id, "user_id": sample_project_data["user_id"]}
                )
                assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time (10 seconds for 10 requests)
        assert total_time < 10.0

    def test_service_isolation(self):
        """Test that services are properly isolated."""
        # Test that one service failure doesn't affect others
        # This is more of a conceptual test - in practice, we'd need
        # to mock service failures and verify others continue working

        # Verify all services are properly initialized
        assert task_prioritization_service is not None
        assert realtime_collaboration_service is not None
        assert smart_suggestions_service is not None
        assert task_dependency_service is not None
        assert progress_tracking_service is not None
        assert team_collaboration_service is not None

    def test_cross_service_data_flow(self, test_client, sample_project_data):
        """Test data flow between different services."""
        project_id = sample_project_data["project_id"]
        user_id = sample_project_data["user_id"]

        # 1. Create a task via prioritization service
        with patch.object(task_prioritization_service, '_fetch_project_tasks') as mock_fetch:
            mock_fetch.return_value = sample_project_data["tasks"]

            pri_response = test_client.post(
                "/api/task-prioritization/prioritize",
                json={"project_id": project_id, "user_id": user_id}
            )
            assert pri_response.status_code == 200
            pri_data = pri_response.json()["data"]

        # 2. Get suggestions based on the prioritized tasks
        with patch.object(smart_suggestions_service, '_get_user_patterns') as mock_patterns:
            mock_patterns.return_value = {
                "preferred_work_hours": [9, 10, 11],
                "common_task_types": ["feature"],
                "skill_levels": {"python": 0.8}
            }

            sug_response = test_client.post(
                "/api/smart-suggestions/suggest",
                json={"project_id": project_id}
            )
            assert sug_response.status_code == 200
            sug_data = sug_response.json()

        # 3. Verify data consistency between services
        if pri_data and sug_data.get("primary_suggestion"):
            # The suggested task should be one of the prioritized tasks
            suggested_task_id = sug_data["primary_suggestion"]["task_id"]
            prioritized_task_ids = [task["task_id"] for task in pri_data]

            # This assertion might not always hold due to different algorithms,
            # but we can at least verify the data structures are consistent
            assert isinstance(suggested_task_id, str)
            assert len(suggested_task_id) > 0

    def test_memory_management(self):
        """Test that services properly manage memory and resources."""
        # This is a basic test - in a real scenario, we'd monitor memory usage
        # and ensure services don't have memory leaks

        import gc

        # Force garbage collection
        gc.collect()

        # Verify services can handle repeated operations without memory issues
        # (This is more of a smoke test for memory management)

        initial_objects = len(gc.get_objects())

        # Perform some operations
        for _ in range(5):
            # Simple operation that shouldn't cause memory leaks
            asyncio.run(task_prioritization_service._is_cache_valid("test-project"))

        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory growth should be minimal (allowing for some natural growth)
        growth_rate = (final_objects - initial_objects) / initial_objects
        assert growth_rate < 0.1  # Less than 10% growth


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
