"""
End-to-end integration tests for complete user workflows
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agentic-workflow'))

from fastapi.testclient import TestClient
from fastapi import FastAPI

@pytest.mark.asyncio
class TestEndToEndWorkflows:
    """Test suite for complete end-to-end user workflows."""

    @pytest.fixture
    async def test_app(self):
        """Create a test FastAPI application."""
        from api.fastapi_server import app
        return app

    @pytest.fixture
    def test_client(self, test_app):
        """Create a test client."""
        return TestClient(test_app)

    async def test_complete_requirement_generation_workflow(self, test_client):
        """Test complete workflow from prompt to generated requirements."""
        # Step 1: User submits feature description
        prompt_data = {
            "prompt": "Create a user authentication system with login, registration, and password reset",
            "provider": "grok",
            "version": "v1"
        }
        
        with patch('api.fastapi_server.generate_requirements_specs') as mock_generate:
            mock_generate.return_value = {
                "requirement_id": "req-123",
                "specs": "Complete authentication system specifications",
                "status": "completed"
            }
            
            response = test_client.post("/api/generate-specs", json=prompt_data)
            assert response.status_code == 200
            
            requirement_id = response.json()["requirement_id"]
        
        # Step 2: Retrieve generated requirements
        response = test_client.get(f"/api/requirements/{requirement_id}")
        assert response.status_code == 200
        
        requirements = response.json()
        assert requirements["id"] == requirement_id
        assert "specs" in requirements
        
        # Step 3: A/B test different versions
        ab_test_data = {
            "prompt": "User authentication system",
            "versions": ["v1", "v1b", "enhanced"],
            "provider": "grok"
        }
        
        with patch('api.fastapi_server.enhanced_ab_testing') as mock_ab_testing:
            mock_ab_testing.run_prompt_comparison.return_value = {
                "test_id": "ab-test-123",
                "winner": "enhanced",
                "scores": {"v1": 0.7, "v1b": 0.8, "enhanced": 0.9}
            }
            
            response = test_client.post("/api/ab-test", json=ab_test_data)
            assert response.status_code == 200
            
            test_result = response.json()
            assert test_result["winner"] == "enhanced"
        
        # Step 4: Publish to marketplace
        listing_data = {
            "title": "Authentication System Requirements",
            "description": "Complete user authentication system specifications",
            "content": {"type": "spec_template", "data": requirements},
            "tags": ["authentication", "security", "user-management"],
            "author": "test-user",
            "pricing": {"amount": 150, "currency": "ZIPPY"}
        }
        
        with patch('api.fastapi_server.marketplace') as mock_marketplace:
            mock_marketplace.create_listing.return_value = "listing-123"
            
            response = test_client.post("/api/marketplace/listings", json=listing_data)
            assert response.status_code == 201
            
            listing_id = response.json()["listing_id"]
        
        # Step 5: Verify marketplace listing
        response = test_client.get(f"/api/marketplace/listings/{listing_id}")
        assert response.status_code == 200
        
        listing = response.json()
        assert listing["title"] == "Authentication System Requirements"
        assert listing["author"] == "test-user"

    async def test_complete_plugin_development_workflow(self, test_client):
        """Test complete workflow for plugin development and deployment."""
        # Step 1: Create plugin code
        plugin_code = """
class AuthenticationPlugin:
    name = "authentication_plugin"
    description = "Plugin for user authentication operations"
    
    def run(self, operation, **kwargs):
        if operation == "login":
            return self._handle_login(kwargs.get("credentials"))
        elif operation == "register":
            return self._handle_registration(kwargs.get("user_data"))
        return {"error": "Unknown operation"}
    
    def _handle_login(self, credentials):
        # Mock login logic
        return {"status": "success", "user_id": "user-123"}
    
    def _handle_registration(self, user_data):
        # Mock registration logic
        return {"status": "success", "user_id": "new-user-456"}
        """
        
        plugin_metadata = {
            "name": "authentication_plugin",
            "description": "Plugin for user authentication operations",
            "author": "plugin-developer",
            "version": "1.0.0",
            "dependencies": [],
            "tags": ["authentication", "security"],
            "license": "MIT"
        }
        
        # Step 2: Verify plugin with trust manager
        with patch('api.fastapi_server.trust_manager') as mock_trust:
            mock_trust.verify_plugin.return_value = {
                "plugin_id": "plugin-123",
                "trust_score": 0.85,
                "verification_status": "verified"
            }
            
            response = test_client.post("/api/plugins/verify", json={
                "plugin_code": plugin_code,
                "metadata": plugin_metadata
            })
            assert response.status_code == 200
            
            verification_result = response.json()
            assert verification_result["verification_status"] == "verified"
            assert verification_result["trust_score"] == 0.85
        
        # Step 3: Register plugin
        with patch('api.fastapi_server.plugin_manager') as mock_plugin_manager:
            mock_plugin_manager.register_tool.return_value = True
            
            response = test_client.post("/api/plugins/register", json={
                "plugin_id": "plugin-123",
                "plugin_code": plugin_code,
                "metadata": plugin_metadata
            })
            assert response.status_code == 200
        
        # Step 4: Test plugin functionality
        with patch('api.fastapi_server.plugin_manager') as mock_plugin_manager:
            mock_plugin_manager.get_tool_by_name.return_value = MagicMock()
            
            response = test_client.post("/api/plugins/execute", json={
                "plugin_name": "authentication_plugin",
                "operation": "login",
                "parameters": {"credentials": {"username": "test", "password": "test123"}}
            })
            assert response.status_code == 200

    async def test_complete_ai_agent_creation_workflow(self, test_client):
        """Test complete workflow for AI agent creation using agentic workflow."""
        # Step 1: Initiate agent creation
        agent_description = {
            "description": "Create an AI agent that can analyze code quality and provide improvement suggestions",
            "capabilities": ["code_analysis", "quality_assessment", "improvement_suggestions"],
            "target_language": "Python"
        }
        
        with patch('api.fastapi_server.archon_graph') as mock_archon:
            mock_archon.agentic_flow.astream.return_value = [
                {"type": "scope", "content": "Agent scope defined"},
                {"type": "architecture", "content": "Agent architecture planned"},
                {"type": "implementation", "content": "Agent code generated"},
                {"type": "testing", "content": "Agent tests created"},
                {"type": "deployment", "content": "Agent ready for deployment"}
            ]
            
            response = test_client.post("/api/agents/create", json=agent_description)
            assert response.status_code == 200
            
            agent_result = response.json()
            assert "agent_id" in agent_result
            assert "status" in agent_result
        
        # Step 2: Monitor agent development progress
        agent_id = agent_result["agent_id"]
        
        with patch('api.fastapi_server.archon_graph') as mock_archon:
            mock_archon.get_agent_status.return_value = {
                "status": "in_progress",
                "current_step": "implementation",
                "progress": 60
            }
            
            response = test_client.get(f"/api/agents/{agent_id}/status")
            assert response.status_code == 200
            
            status = response.json()
            assert status["status"] == "in_progress"
            assert status["progress"] == 60
        
        # Step 3: Deploy completed agent
        with patch('api.fastapi_server.archon_graph') as mock_archon:
            mock_archon.deploy_agent.return_value = {
                "status": "deployed",
                "endpoint": "/api/agents/code-analyzer",
                "capabilities": ["code_analysis", "quality_assessment"]
            }
            
            response = test_client.post(f"/api/agents/{agent_id}/deploy")
            assert response.status_code == 200
            
            deployment = response.json()
            assert deployment["status"] == "deployed"
            assert "endpoint" in deployment
        
        # Step 4: Test deployed agent
        test_code = "def example_function():\n    return 'Hello, World!'"
        
        with patch('api.fastapi_server.archon_graph') as mock_archon:
            mock_archon.execute_agent.return_value = {
                "analysis": "Code quality is good",
                "suggestions": ["Consider adding type hints", "Add docstring"],
                "score": 8.5
            }
            
            response = test_client.post(f"/api/agents/{agent_id}/execute", json={
                "input": test_code,
                "operation": "analyze_code"
            })
            assert response.status_code == 200
            
            result = response.json()
            assert "analysis" in result
            assert "suggestions" in result
            assert "score" in result

    async def test_complete_marketplace_trading_workflow(self, test_client):
        """Test complete workflow for marketplace trading."""
        # Step 1: Create marketplace listing
        listing_data = {
            "title": "Advanced Code Quality Analyzer",
            "description": "AI-powered code quality analysis tool",
            "content": {"type": "ai_tool", "data": "Tool implementation"},
            "tags": ["ai", "code-quality", "analysis"],
            "author": "ai-developer",
            "pricing": {"amount": 200, "currency": "ZIPPY"}
        }
        
        with patch('api.fastapi_server.marketplace') as mock_marketplace:
            mock_marketplace.create_listing.return_value = "listing-456"
            
            response = test_client.post("/api/marketplace/listings", json=listing_data)
            assert response.status_code == 201
            
            listing_id = response.json()["listing_id"]
        
        # Step 2: Browse marketplace
        with patch('api.fastapi_server.marketplace') as mock_marketplace:
            mock_marketplace.search_listings.return_value = [
                {
                    "listing_id": listing_id,
                    "title": "Advanced Code Quality Analyzer",
                    "author": "ai-developer",
                    "rating": 4.8,
                    "price": 200
                }
            ]
            
            response = test_client.get("/api/marketplace/search?tags=ai,code-quality")
            assert response.status_code == 200
            
            search_results = response.json()
            assert len(search_results) == 1
            assert search_results[0]["title"] == "Advanced Code Quality Analyzer"
        
        # Step 3: Purchase listing
        buyer_wallet = "buyer-wallet-789"
        
        with patch('api.fastapi_server.marketplace') as mock_marketplace:
            mock_marketplace.purchase_listing.return_value = "transaction-123"
            
            response = test_client.post(f"/api/marketplace/listings/{listing_id}/purchase", json={
                "buyer_wallet": buyer_wallet
            })
            assert response.status_code == 200
            
            transaction = response.json()
            assert "transaction_id" in transaction
        
        # Step 4: Download purchased content
        with patch('api.fastapi_server.marketplace') as mock_marketplace:
            mock_marketplace.get_listing.return_value = {
                "listing_id": listing_id,
                "content": {"type": "ai_tool", "data": "Tool implementation"},
                "download_url": "/api/marketplace/download/token-123"
            }
            
            response = test_client.get(f"/api/marketplace/listings/{listing_id}")
            assert response.status_code == 200
            
            listing = response.json()
            assert "download_url" in listing
        
        # Step 5: Rate and review
        review_data = {
            "rating": 5,
            "comment": "Excellent tool, very useful for code quality analysis!",
            "reviewer": buyer_wallet
        }
        
        with patch('api.fastplace_server.marketplace') as mock_marketplace:
            mock_marketplace.add_review.return_value = True
            
            response = test_client.post(f"/api/marketplace/listings/{listing_id}/reviews", json=review_data)
            assert response.status_code == 200

    async def test_complete_error_recovery_workflow(self, test_client):
        """Test complete workflow for error detection and recovery."""
        # Step 1: Simulate system error
        with patch('api.fastapi_server.database_manager') as mock_db:
            mock_db.create_requirement.side_effect = Exception("Database connection failed")
            
            response = test_client.post("/api/requirements", json={
                "title": "Test Requirement",
                "description": "Test description"
            })
            assert response.status_code == 500
        
        # Step 2: Check system health
        response = test_client.get("/api/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        
        # Step 3: Trigger diagnostic agent
        with patch('api.fastapi_server.diagnostic_agent') as mock_diagnostic:
            mock_diagnostic.analyze_error.return_value = {
                "error_type": "database_connection",
                "severity": "high",
                "recommended_action": "restart_database_service",
                "estimated_recovery_time": "5 minutes"
            }
            
            response = test_client.post("/api/diagnostics/analyze", json={
                "error_log": "Database connection failed",
                "timestamp": "2024-01-01T00:00:00Z"
            })
            assert response.status_code == 200
            
            diagnosis = response.json()
            assert diagnosis["error_type"] == "database_connection"
            assert diagnosis["severity"] == "high"
        
        # Step 4: Execute recovery action
        with patch('api.fastapi_server.diagnostic_agent') as mock_diagnostic:
            mock_diagnostic.execute_recovery.return_value = {
                "action": "restart_database_service",
                "status": "completed",
                "result": "Database service restarted successfully"
            }
            
            response = test_client.post("/api/diagnostics/recover", json={
                "action": "restart_database_service"
            })
            assert response.status_code == 200
            
            recovery = response.json()
            assert recovery["status"] == "completed"
        
        # Step 5: Verify system recovery
        response = test_client.get("/api/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"

    async def test_complete_performance_monitoring_workflow(self, test_client):
        """Test complete workflow for performance monitoring and optimization."""
        # Step 1: Generate load for testing
        for i in range(10):
            test_client.get("/api/health")
        
        # Step 2: Check performance metrics
        response = test_client.get("/api/performance/stats")
        assert response.status_code == 200
        
        perf_stats = response.json()
        assert "response_times" in perf_stats
        assert "throughput" in perf_stats
        assert "error_rates" in perf_stats
        
        # Step 3: Analyze performance bottlenecks
        with patch('api.fastapi_server.performance_analyzer') as mock_analyzer:
            mock_analyzer.analyze_bottlenecks.return_value = {
                "bottlenecks": [
                    {
                        "endpoint": "/api/requirements",
                        "avg_response_time": 1500,
                        "recommendation": "Add database indexing"
                    }
                ],
                "optimization_score": 0.7
            }
            
            response = test_client.post("/api/performance/analyze")
            assert response.status_code == 200
            
            analysis = response.json()
            assert "bottlenecks" in analysis
            assert "optimization_score" in analysis
        
        # Step 4: Apply performance optimizations
        with patch('api.fastapi_server.performance_optimizer') as mock_optimizer:
            mock_optimizer.apply_optimizations.return_value = {
                "optimizations_applied": ["database_indexing", "query_optimization"],
                "expected_improvement": "30% reduction in response time"
            }
            
            response = test_client.post("/api/performance/optimize")
            assert response.status_code == 200
            
            optimization = response.json()
            assert "optimizations_applied" in optimization
        
        # Step 5: Verify performance improvement
        response = test_client.get("/api/performance/stats")
        assert response.status_code == 200
        
        new_perf_stats = response.json()
        # Should show improved metrics
        assert "response_times" in new_perf_stats
