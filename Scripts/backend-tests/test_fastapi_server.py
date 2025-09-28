"""
Tests for the FastAPI server endpoints and functionality
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
class TestFastAPIServer:
    """Test suite for FastAPI server endpoints."""

    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    async def test_generate_specs_endpoint(self, async_client: AsyncClient, sample_requirement_data):
        """Test requirements generation endpoint."""
        with patch('api.fastapi_server.generate_requirements_specs') as mock_generate:
            mock_generate.return_value = {
                "requirement_id": "test-123",
                "specs": "Generated specifications",
                "status": "completed"
            }
            
            response = await async_client.post(
                "/api/generate-specs",
                json={
                    "prompt": "Test feature description",
                    "provider": "grok",
                    "version": "v1"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "requirement_id" in data
            assert "specs" in data
            assert "status" in data

    async def test_ab_testing_endpoint(self, async_client: AsyncClient, sample_ab_test_data):
        """Test A/B testing endpoint."""
        with patch('api.fastapi_server.enhanced_ab_testing') as mock_ab_testing:
            mock_ab_testing.run_prompt_comparison.return_value = {
                "test_id": "test-ab-123",
                "winner": "v1",
                "scores": {"v1": 0.85, "v2": 0.7}
            }
            
            response = await async_client.post(
                "/api/ab-test",
                json=sample_ab_test_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "test_id" in data
            assert "winner" in data

    async def test_requirements_crud(self, async_client: AsyncClient, sample_requirement_data):
        """Test CRUD operations for requirements."""
        # Create requirement
        with patch('api.fastapi_server.database_manager') as mock_db:
            mock_db.create_requirement.return_value = {
                **sample_requirement_data,
                "id": "test-req-123"
            }
            
            response = await async_client.post(
                "/api/requirements",
                json=sample_requirement_data
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["id"] == "test-req-123"

        # Get requirement
        with patch('api.fastapi_server.database_manager') as mock_db:
            mock_db.get_requirement.return_value = {
                **sample_requirement_data,
                "id": "test-req-123"
            }
            
            response = await async_client.get("/api/requirements/test-req-123")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == "test-req-123"

        # List requirements
        with patch('api.fastapi_server.database_manager') as mock_db:
            mock_db.list_requirements.return_value = [
                {**sample_requirement_data, "id": "test-req-123"}
            ]
            
            response = await async_client.get("/api/requirements")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "test-req-123"

    async def test_plugin_management(self, async_client: AsyncClient, sample_plugin_data):
        """Test plugin management endpoints."""
        # Verify plugin
        with patch('api.fastapi_server.trust_manager') as mock_trust:
            mock_trust.verify_plugin.return_value = {
                "plugin_id": "test-plugin-123",
                "trust_score": 0.8,
                "verification_status": "verified"
            }
            
            response = await async_client.post(
                "/api/plugins/verify",
                json=sample_plugin_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["verification_status"] == "verified"

    async def test_marketplace_operations(self, async_client: AsyncClient):
        """Test marketplace endpoints."""
        # Create listing
        listing_data = {
            "title": "Test Listing",
            "description": "Test description",
            "content": {"type": "spec_template"},
            "tags": ["test", "template"],
            "author": "test-author",
            "pricing": {"amount": 100, "currency": "ZIPPY"}
        }
        
        with patch('api.fastapi_server.marketplace') as mock_marketplace:
            mock_marketplace.create_listing.return_value = "test-listing-123"
            
            response = await async_client.post(
                "/api/marketplace/listings",
                json=listing_data
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["listing_id"] == "test-listing-123"

    async def test_error_handling(self, async_client: AsyncClient):
        """Test error handling and validation."""
        # Test invalid JSON
        response = await async_client.post(
            "/api/generate-specs",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test missing required fields
        response = await async_client.post(
            "/api/generate-specs",
            json={"provider": "grok"}  # Missing prompt
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_rate_limiting(self, async_client: AsyncClient):
        """Test rate limiting functionality."""
        # This would test the rate limiting middleware
        # Implementation depends on the specific rate limiting setup
        pass

    async def test_authentication(self, async_client: AsyncClient):
        """Test authentication and authorization."""
        # Test protected endpoints without authentication
        response = await async_client.get("/api/admin/stats")
        # Should return 401 or 403 depending on implementation
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are properly set."""
        response = await async_client.options("/api/health")
        # Check if CORS headers are present
        assert "access-control-allow-origin" in response.headers

    async def test_metrics_endpoint(self, async_client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await async_client.get("/metrics")
        # Should return metrics in Prometheus format
        assert response.status_code == status.HTTP_200_OK
        assert "http_requests_total" in response.text

    async def test_database_connection_handling(self, async_client: AsyncClient):
        """Test database connection error handling."""
        with patch('api.fastapi_server.database_manager') as mock_db:
            mock_db.create_requirement.side_effect = Exception("Database connection failed")
            
            response = await async_client.post(
                "/api/requirements",
                json={"title": "Test", "description": "Test"}
            )
            
            # Should handle database errors gracefully
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    async def test_ai_provider_fallback(self, async_client: AsyncClient):
        """Test AI provider fallback mechanism."""
        with patch('api.fastapi_server.multi_provider_ai') as mock_ai:
            # Mock primary provider failure
            mock_ai.generate_with_fallback.return_value = {
                "content": "Generated content",
                "provider": "fallback-provider",
                "success": True
            }
            
            response = await async_client.post(
                "/api/generate-specs",
                json={"prompt": "Test prompt", "provider": "openai"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "specs" in data

    async def test_plugin_loading(self, async_client: AsyncClient):
        """Test dynamic plugin loading."""
        with patch('api.fastapi_server.plugin_manager') as mock_plugin_manager:
            mock_plugin_manager.load_plugins.return_value = ["plugin1", "plugin2"]
            
            response = await async_client.get("/api/plugins")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2

    async def test_trust_scoring(self, async_client: AsyncClient):
        """Test trust scoring functionality."""
        with patch('api.fastapi_server.trust_manager') as mock_trust:
            mock_trust.calculate_trust_score.return_value = 0.85
            
            response = await async_client.post(
                "/api/trust/calculate",
                json={"plugin_code": "def test(): pass", "metadata": {"name": "test"}}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["trust_score"] == 0.85

    async def test_performance_monitoring(self, async_client: AsyncClient):
        """Test performance monitoring endpoints."""
        response = await async_client.get("/api/performance/stats")
        # Should return performance statistics
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response_times" in data
        assert "throughput" in data

    async def test_security_headers(self, async_client: AsyncClient):
        """Test security headers are properly set."""
        response = await async_client.get("/api/health")
        # Check for security headers
        headers = response.headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "x-xss-protection" in headers
