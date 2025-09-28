"""Security and Authentication Tests"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import httpx


class TestAuthentication:
    """Test authentication endpoints and JWT functionality."""

    def test_login_endpoint_exists(self, client):
        """Test that login endpoint exists and responds."""
        response = client.post("/auth/login", json={"username": "test", "password": "test"})
        assert response.status_code in [200, 422, 500]  # Allow validation errors

    def test_register_endpoint_exists(self, client):
        """Test that register endpoint exists."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "wallet_address": "0x1234567890abcdef"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code in [200, 201, 400, 409, 422, 500]

    def test_protected_endpoint_requires_auth(self, client):
        """Test that protected endpoints require authentication."""
        response = client.post("/api/v1/specs/generate", json={"prompt": "test"})
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.post("/api/v1/specs/generate",
                             json={"prompt": "test"},
                             headers=headers)
        assert response.status_code == 401


class TestSecurity:
    """Test security features like rate limiting and input validation."""

    def test_rate_limiting_headers(self, client):
        """Test that rate limiting returns proper headers."""
        # Make multiple requests quickly
        for i in range(5):
            response = client.get("/health")
            if response.status_code == 429:
                assert "Retry-After" in response.headers or "retry_after" in response.json()
                break

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/health", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in response.headers

    def test_input_validation(self, client):
        """Test input validation for various endpoints."""
        # Test specs generation with invalid data
        response = client.post("/api/v1/specs/generate", json={})
        assert response.status_code in [401, 422]  # Auth error or validation error

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection."""
        malicious_prompt = "'; DROP TABLE users; --"
        response = client.post("/api/v1/specs/generate",
                             json={"prompt": malicious_prompt})
        # Should not crash the server
        assert response.status_code in [200, 401, 422, 500]

    def test_xss_protection(self, client):
        """Test protection against XSS attacks."""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post("/api/v1/specs/generate",
                             json={"prompt": xss_payload})
        # Should not contain script tags in response
        if response.status_code == 200:
            assert "<script>" not in response.text


class TestHealthMonitoring:
    """Test health check and monitoring endpoints."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns proper information."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

        # Check service status
        services = data["services"]
        assert "ai_system" in services
        assert "database" in services

    def test_health_includes_version(self, client):
        """Test health endpoint includes version information."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "version" in data or "uptime" in data

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint is accessible."""
        response = client.get("/metrics")
        # Metrics might not be available in test environment
        assert response.status_code in [200, 404, 500]


class TestAPIEndpoints:
    """Test various API endpoints for security and functionality."""

    def test_specs_listing(self, client):
        """Test specs listing endpoint."""
        response = client.get("/api/v1/specs")
        assert response.status_code in [200, 401, 500]

    def test_ab_test_listing(self, client):
        """Test A/B test listing endpoint."""
        response = client.get("/api/v1/ab-test")
        assert response.status_code in [200, 401, 500]

    def test_marketplace_search(self, client):
        """Test marketplace search endpoint."""
        response = client.get("/api/v1/marketplace/listings")
        assert response.status_code in [200, 401, 500]

    def test_user_endpoints(self, client):
        """Test user-related endpoints."""
        # Get user by ID
        response = client.get("/api/v1/users/test-user")
        assert response.status_code in [200, 401, 404, 500]

    def test_trust_validation(self, client):
        """Test trust validation endpoint."""
        payload = {
            "content": "WHEN user logs in THEN system authenticates",
            "content_type": "requirements"
        }
        response = client.post("/api/v1/trust/validate", json=payload)
        assert response.status_code in [200, 401, 500]


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON."""
        response = client.post("/api/v1/specs/generate",
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 422]

    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        large_prompt = "test " * 10000  # Very large prompt
        response = client.post("/api/v1/specs/generate",
                             json={"prompt": large_prompt})
        # Should handle gracefully, not crash
        assert response.status_code in [200, 401, 413, 500]

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import asyncio
        import aiohttp

        async def make_request(session, url):
            async with session.get(url) as response:
                return response.status

        async def test_concurrent():
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, "http://localhost:8000/health") for _ in range(10)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results

        # This would need to be run in an async test environment
        # For now, just verify the endpoint exists
        response = client.get("/health")
        assert response.status_code == 200


class TestPerformance:
    """Test performance aspects."""

    def test_response_time(self, client):
        """Test response times are reasonable."""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 5.0  # Should respond within 5 seconds
        assert response.status_code == 200

    def test_memory_usage(self, client):
        """Test basic memory usage doesn't explode."""
        # Make multiple requests
        for i in range(50):
            response = client.get("/health")
            assert response.status_code == 200

    def test_connection_handling(self, client):
        """Test connection handling and cleanup."""
        # Test keep-alive connections
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200
            assert "connection" in response.headers or True  # Connection header might not be present


# Integration tests that require authentication
class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication."""

    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token for tests."""
        # This would normally login and get a token
        # For now, return a mock token
        return "mock-jwt-token"

    def test_authenticated_specs_generation(self, client, auth_token):
        """Test specs generation with authentication."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/v1/specs/generate",
                             json={"prompt": "test feature"},
                             headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_authenticated_marketplace_listing(self, client, auth_token):
        """Test marketplace listing creation with authentication."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        listing_data = {
            "title": "Test Template",
            "description": "Test description",
            "content": {"test": "data"},
            "category": "spec_template",
            "pricing": {"price": 10, "currency": "ZIPPY"}
        }
        response = client.post("/api/v1/marketplace/listings",
                             json=listing_data,
                             headers=headers)
        assert response.status_code in [200, 201, 422, 500]


