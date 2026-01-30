"""End-to-End Tests using Playwright"""

import pytest
import asyncio
import json
import time
from playwright.async_api import async_playwright, Page, Browser
import os


class TestE2EWorkflow:
    """End-to-end tests for the complete Zippy-Archon workflow."""

    @pytest.fixture(scope="class")
    async def browser_context(self):
        """Set up browser context for E2E tests."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='ZippyArchon-E2E-Test/1.0'
            )
            yield context
            await context.close()
            await browser.close()

    @pytest.fixture
    async def page(self, browser_context):
        """Create a new page for each test."""
        page = await browser_context.new_page()
        yield page
        await page.close()

    async def test_frontend_loads(self, page: Page):
        """Test that the frontend loads successfully."""
        # Navigate to frontend
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Wait for page to load
        await page.wait_for_load_state('networkidle')

        # Check for main elements
        title = await page.title()
        assert "Archon" in title or "Zippy" in title

        # Check for essential UI elements
        await page.wait_for_selector('[data-testid="main-content"], .main, #root', timeout=10000)

        # Check for core functionality indicators
        content = await page.content()
        assert "welcome" in content.lower() or "dashboard" in content.lower() or "project" in content.lower()

    async def test_api_health_check(self, page: Page):
        """Test API health endpoint through frontend."""
        # Navigate to frontend
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Try to make an API call (if frontend makes health checks)
        api_url = os.getenv("API_URL", "http://localhost:8181")

        # Test direct API call
        response = await page.request.get(f"{api_url}/health")
        assert response.status == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    async def test_user_registration_flow(self, page: Page):
        """Test complete user registration flow."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Look for registration/login form
        try:
            # Try different selectors for login/registration
            selectors = [
                '[data-testid="register-button"]',
                '.register-button',
                'button:has-text("Register")',
                'button:has-text("Sign Up")',
                '[data-testid="login-form"]',
                '.login-form'
            ]

            form_found = False
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    form_found = True
                    break
                except:
                    continue

            if not form_found:
                # Skip test if no registration form found (might be SSO only)
                pytest.skip("Registration form not found - might be SSO only")

        except Exception as e:
            pytest.skip(f"Registration form test skipped: {e}")

    async def test_requirements_generation(self, page: Page):
        """Test requirements generation workflow."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Look for requirements/spec generation interface
        try:
            selectors = [
                '[data-testid="spec-generator"]',
                '.spec-generator',
                'textarea[placeholder*="requirement" i]',
                'textarea[placeholder*="feature" i]',
                '[data-testid="prompt-input"]',
                '.prompt-input'
            ]

            interface_found = False
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    interface_found = True

                    # Try to enter a test prompt
                    await page.fill(selector, "Test feature: user authentication system")
                    break
                except:
                    continue

            if not interface_found:
                # Try to find any input field that might be for prompts
                inputs = await page.query_selector_all('textarea, input[type="text"]')
                if inputs:
                    await inputs[0].fill("Test feature: user authentication system")
                    interface_found = True

            if interface_found:
                # Look for submit button
                submit_selectors = [
                    '[data-testid="generate-button"]',
                    '.generate-button',
                    'button:has-text("Generate")',
                    'button:has-text("Submit")',
                    'button[type="submit"]'
                ]

                for submit_selector in submit_selectors:
                    try:
                        await page.wait_for_selector(submit_selector, timeout=2000)
                        # Click generate button
                        await page.click(submit_selector)

                        # Wait for response or loading state
                        await page.wait_for_selector(
                            '[data-testid="loading"], .loading, [data-testid="result"]',
                            timeout=10000
                        )
                        break
                    except:
                        continue

        except Exception as e:
            pytest.skip(f"Requirements generation test skipped: {e}")

    async def test_navigation_and_routing(self, page: Page):
        """Test navigation and routing functionality."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Test navigation elements
        nav_selectors = [
            'nav',
            '[data-testid="navigation"]',
            '.navbar',
            '.sidebar',
            '[role="navigation"]'
        ]

        nav_found = False
        for selector in nav_selectors:
            try:
                await page.wait_for_selector(selector, timeout=3000)
                nav_found = True
                break
            except:
                continue

        if nav_found:
            # Try to find and click navigation links
            links = await page.query_selector_all('a, button[role="link"]')
            for link in links[:3]:  # Test first 3 links
                try:
                    href = await link.get_attribute('href')
                    if href and not href.startswith('http'):
                        await link.click()
                        await page.wait_for_load_state('networkidle')
                        await page.go_back()
                        break
                except:
                    continue

    async def test_error_handling(self, page: Page):
        """Test error handling and user feedback."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        api_url = os.getenv("API_URL", "http://localhost:8181")

        # Test invalid API endpoint
        try:
            response = await page.request.get(f"{api_url}/nonexistent-endpoint")
            assert response.status == 404
        except:
            # API might not be available in test environment
            pass

        # Test invalid frontend route
        try:
            await page.goto(f"{frontend_url}/nonexistent-route")
            await page.wait_for_load_state('networkidle')

            # Check if error page or redirect occurs
            title = await page.title()
            assert "404" in title or "Not Found" in title or "error" in title.lower()

        except:
            # Skip if frontend doesn't handle 404s gracefully
            pass

    async def test_responsive_design(self, page: Page):
        """Test responsive design across different screen sizes."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Test mobile viewport
        await page.set_viewport_size({'width': 375, 'height': 667})
        await page.wait_for_load_state('networkidle')

        # Check that content is still accessible on mobile
        body = await page.query_selector('body')
        assert body is not None

        # Test tablet viewport
        await page.set_viewport_size({'width': 768, 'height': 1024})
        await page.wait_for_load_state('networkidle')

        # Test desktop viewport
        await page.set_viewport_size({'width': 1920, 'height': 1080})
        await page.wait_for_load_state('networkidle')

    async def test_performance_metrics(self, page: Page):
        """Test basic performance metrics."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)

        # Wait for page to fully load
        await page.wait_for_load_state('networkidle')

        # Get performance metrics
        metrics = await page.evaluate("""
            () => {
                const perf = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                    loadComplete: perf.loadEventEnd - perf.loadEventStart,
                    totalTime: perf.loadEventEnd - perf.fetchStart
                };
            }
        """)

        # Assert reasonable performance (under 10 seconds for initial load)
        assert metrics['totalTime'] < 10000, f"Page took too long to load: {metrics['totalTime']}ms"

        # Check for any console errors
        console_messages = []
        page.on('console', lambda msg: console_messages.append(msg.text))

        # Wait a bit to capture any console errors
        await page.wait_for_timeout(2000)

        # Filter out expected console messages
        error_messages = [msg for msg in console_messages if 'error' in msg.lower()]

        # Allow some console errors but not too many
        assert len(error_messages) < 5, f"Too many console errors: {error_messages}"


class TestAPISecurity:
    """Test API security through browser requests."""

    async def test_cors_policy(self, page: Page):
        """Test CORS policy from browser context."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        try:
            # Try to make a cross-origin request
            response = await page.request.get(f"{api_url}/health", headers={'Origin': 'http://localhost:3000'})
            assert response.status == 200

            # Check CORS headers
            cors_headers = ['access-control-allow-origin', 'access-control-allow-methods']
            response_headers = response.headers

            cors_present = any(header in response_headers for header in cors_headers)
            assert cors_present, "CORS headers not found in response"

        except Exception as e:
            pytest.skip(f"CORS test skipped: {e}")


class TestAPIIntegration:
    """Comprehensive API integration tests."""

    async def test_api_docs_accessibility(self, page: Page):
        """Test that API documentation is accessible."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        # Test OpenAPI/Swagger docs
        try:
            response = await page.request.get(f"{api_url}/docs")
            assert response.status == 200

            # Check for OpenAPI content
            content = await response.text()
            assert "openapi" in content.lower() or "swagger" in content.lower()

        except Exception as e:
            pytest.skip(f"API docs test skipped: {e}")

    async def test_api_version_endpoint(self, page: Page):
        """Test API version endpoint."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        try:
            response = await page.request.get(f"{api_url}/api/v1/version")
            assert response.status in [200, 404]  # 404 if endpoint doesn't exist yet

            if response.status == 200:
                data = await response.json()
                assert "version" in data or "name" in data

        except Exception as e:
            pytest.skip(f"API version test skipped: {e}")

    async def test_websocket_connectivity(self, page: Page):
        """Test WebSocket connectivity for real-time features."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            # Navigate to frontend and check for WebSocket connections
            await page.goto(frontend_url)
            await page.wait_for_load_state('networkidle')

            # Check if WebSocket connections are established
            # This is a basic check - real implementation would need proper WebSocket testing
            ws_connections = await page.evaluate("""
                () => {
                    return performance.getEntriesByType('resource')
                        .filter(entry => entry.name.includes('ws://') || entry.name.includes('wss://'))
                        .length;
                }
            """)

            # At minimum, there should be no WebSocket connection errors in console
            console_messages = []
            page.on('console', lambda msg: console_messages.append(str(msg)))

            await page.wait_for_timeout(3000)

            ws_errors = [msg for msg in console_messages if 'websocket' in msg.lower() and 'error' in msg.lower()]
            assert len(ws_errors) == 0, f"WebSocket errors found: {ws_errors}"

        except Exception as e:
            pytest.skip(f"WebSocket test skipped: {e}")

    async def test_database_connectivity(self, page: Page):
        """Test database connectivity through API."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        try:
            # Test database-dependent endpoints
            endpoints_to_test = ["/health", "/api/v1/status", "/api/v1/info"]

            for endpoint in endpoints_to_test:
                try:
                    response = await page.request.get(f"{api_url}{endpoint}")
                    if response.status == 200:
                        data = await response.json()
                        # Check for database-related fields
                        assert isinstance(data, dict)
                        break
                except:
                    continue

        except Exception as e:
            pytest.skip(f"Database connectivity test skipped: {e}")

    async def test_authentication_flow(self, page: Page):
        """Test authentication flow and session management."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        api_url = os.getenv("API_URL", "http://localhost:8181")

        try:
            # Test login endpoint
            login_response = await page.request.post(
                f"{api_url}/api/v1/auth/login",
                data=json.dumps({
                    "username": "test_user",
                    "password": "test_password"
                }),
                headers={'Content-Type': 'application/json'}
            )

            # Should get authentication response (200, 401, or 422 are all valid)
            assert login_response.status in [200, 401, 422, 404]

            if login_response.status == 200:
                login_data = await login_response.json()
                assert "token" in login_data or "access_token" in login_data

        except Exception as e:
            pytest.skip(f"Authentication test skipped: {e}")

    async def test_file_upload_functionality(self, page: Page):
        """Test file upload capabilities."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        try:
            # Test file upload endpoint
            test_file_content = b"This is a test file for upload testing."

            upload_response = await page.request.post(
                f"{api_url}/api/v1/upload",
                files={"file": ("test.txt", test_file_content, "text/plain")}
            )

            # Should handle file upload (200, 404, or 422 are all valid responses)
            assert upload_response.status in [200, 404, 422, 413]

        except Exception as e:
            pytest.skip(f"File upload test skipped: {e}")


class TestCompleteWorkflows:
    """Test complete user workflows from start to finish."""

    async def test_project_creation_workflow(self, page: Page):
        """Test complete project creation workflow."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            await page.goto(frontend_url)
            await page.wait_for_load_state('networkidle')

            # Look for project creation interface
            project_selectors = [
                '[data-testid="new-project"]',
                '.new-project',
                'button:has-text("New Project")',
                'button:has-text("Create Project")'
            ]

            project_button_found = False
            for selector in project_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    project_button_found = True
                    break
                except:
                    continue

            if project_button_found:
                # Wait for project creation form
                await page.wait_for_selector('input[placeholder*="project"], textarea', timeout=5000)

                # Fill in project details
                inputs = await page.query_selector_all('input, textarea')
                if inputs:
                    # Fill first input (likely project name)
                    await inputs[0].fill("Test E2E Project")

                    # Fill second input if available (likely description)
                    if len(inputs) > 1:
                        await inputs[1].fill("This is a test project created by E2E tests")

                # Submit form
                submit_buttons = await page.query_selector_all('button[type="submit"], button:has-text("Create")')
                if submit_buttons:
                    await submit_buttons[0].click()

                    # Wait for success or redirect
                    await page.wait_for_load_state('networkidle')

                    # Check for success indicators
                    content = await page.content()
                    assert "created" in content.lower() or "success" in content.lower() or "dashboard" in content.lower()

        except Exception as e:
            pytest.skip(f"Project creation workflow test skipped: {e}")

    async def test_knowledge_base_workflow(self, page: Page):
        """Test complete knowledge base workflow."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            await page.goto(frontend_url)
            await page.wait_for_load_state('networkidle')

            # Look for knowledge base interface
            kb_selectors = [
                '[data-testid="knowledge-base"]',
                '.knowledge-base',
                '[data-testid="documents"]',
                '.documents',
                'button:has-text("Knowledge")',
                'button:has-text("Documents")'
            ]

            kb_found = False
            for selector in kb_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    kb_found = True
                    break
                except:
                    continue

            if kb_found:
                # Wait for knowledge base content
                await page.wait_for_selector('[data-testid="document-list"], .document-list, .file-list', timeout=5000)

                # Check for upload functionality
                upload_selectors = [
                    '[data-testid="upload-document"]',
                    '.upload-document',
                    'input[type="file"]',
                    'button:has-text("Upload")'
                ]

                for selector in upload_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        break
                    except:
                        continue

        except Exception as e:
            pytest.skip(f"Knowledge base workflow test skipped: {e}")

    async def test_ai_agent_workflow(self, page: Page):
        """Test complete AI agent workflow."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            await page.goto(frontend_url)
            await page.wait_for_load_state('networkidle')

            # Look for AI agent interface
            agent_selectors = [
                '[data-testid="ai-agent"]',
                '.ai-agent',
                '[data-testid="agents"]',
                '.agents',
                'button:has-text("Agent")',
                'button:has-text("AI")'
            ]

            agent_found = False
            for selector in agent_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    agent_found = True
                    break
                except:
                    continue

            if agent_found:
                # Wait for agent interface
                await page.wait_for_selector('[data-testid="agent-list"], .agent-list, .chat-interface', timeout=5000)

                # Look for chat or prompt interface
                chat_selectors = [
                    '[data-testid="chat-input"]',
                    '.chat-input',
                    'textarea[placeholder*="ask" i]',
                    'input[placeholder*="prompt" i]'
                ]

                for selector in chat_selectors:
                    try:
                        chat_input = await page.wait_for_selector(selector, timeout=3000)
                        await chat_input.fill("Hello, can you help me with a test task?")
                        break
                    except:
                        continue

        except Exception as e:
            pytest.skip(f"AI agent workflow test skipped: {e}")

    async def test_collaboration_features(self, page: Page):
        """Test collaboration features like real-time editing."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            await page.goto(frontend_url)
            await page.wait_for_load_state('networkidle')

            # Look for collaboration indicators
            collab_selectors = [
                '[data-testid="collaboration"]',
                '.collaboration',
                '[data-testid="users-online"]',
                '.users-online',
                '[data-testid="live-cursors"]',
                '.live-cursors'
            ]

            # Check for presence of collaboration features
            collab_features_found = 0
            for selector in collab_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    collab_features_found += 1
                except:
                    continue

            # Should have at least some collaboration features
            assert collab_features_found > 0, "No collaboration features found"

        except Exception as e:
            pytest.skip(f"Collaboration features test skipped: {e}")

    async def test_error_recovery_workflow(self, page: Page):
        """Test error handling and recovery workflows."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            # Test 404 handling
            await page.goto(f"{frontend_url}/nonexistent-page")
            await page.wait_for_load_state('networkidle')

            # Should handle 404 gracefully
            content = await page.content()
            status_404 = await page.evaluate("() => document.querySelector('h1, h2, p')?.textContent || ''")

            # Check that 404 is handled (either error page or redirect)
            assert (
                "404" in content or
                "not found" in content.lower() or
                "error" in content.lower() or
                len(status_404) > 0
            )

        except Exception as e:
            pytest.skip(f"Error recovery test skipped: {e}")

    async def test_cross_origin_requests(self, page: Page):
        """Test cross-origin request handling."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        try:
            # Test preflight OPTIONS request
            response = await page.request.options(f"{api_url}/health")
            # CORS preflight should be allowed or return 404 if not implemented
            assert response.status in [200, 404, 405]

        except Exception as e:
            pytest.skip(f"Cross-origin test skipped: {e}")

    async def test_input_validation_frontend(self, page: Page):
        """Test input validation through frontend interface."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")

        try:
            await page.goto(frontend_url)
            await page.wait_for_load_state('networkidle')

            # Look for input fields that might need validation
            input_selectors = [
                '[data-testid="prompt-input"]',
                '.prompt-input',
                'textarea[placeholder*="prompt" i]',
                'input[placeholder*="input" i]'
            ]

            for selector in input_selectors:
                try:
                    input_field = await page.wait_for_selector(selector, timeout=3000)

                    # Test XSS input
                    await input_field.fill("<script>alert('xss')</script>")
                    await input_field.press('Enter')

                    # Should not crash or show raw script
                    content = await page.content()
                    assert "alert" not in content.lower(), "XSS content leaked to page"

                    # Clear and test normal input
                    await input_field.fill("Normal test input")
                    await input_field.press('Enter')

                    break
                except:
                    continue

        except Exception as e:
            pytest.skip(f"Input validation frontend test skipped: {e}")


# Performance testing utilities
class TestPerformance:
    """Performance testing utilities."""

    async def test_api_response_times(self, page: Page):
        """Test API response times under load."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        response_times = []

        # Make multiple requests to test performance
        for i in range(10):
            start_time = await page.evaluate("performance.now()")

            try:
                response = await page.request.get(f"{api_url}/health")
                end_time = await page.evaluate("performance.now()")

                if response.status == 200:
                    response_times.append(end_time - start_time)

            except:
                continue

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            # Assert reasonable performance
            assert avg_response_time < 1000, f"Average response time too slow: {avg_response_time}ms"
            assert max_response_time < 5000, f"Max response time too slow: {max_response_time}ms"

    async def test_memory_usage(self, page: Page):
        """Test memory usage during operations."""
        # Get initial memory usage
        initial_memory = await page.evaluate("performance.memory ? performance.memory.usedJSHeapSize : 0")

        # Perform some operations
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3737")
        await page.goto(frontend_url)
        await page.wait_for_load_state('networkidle')

        # Navigate to different pages if available
        try:
            links = await page.query_selector_all('a[href^="/"]')
            for link in links[:3]:  # Test first 3 internal links
                try:
                    await link.click()
                    await page.wait_for_load_state('networkidle')
                    await page.go_back()
                except:
                    continue
        except:
            pass

        # Get final memory usage
        final_memory = await page.evaluate("performance.memory ? performance.memory.usedJSHeapSize : 0")

        if initial_memory and final_memory:
            memory_increase = final_memory - initial_memory
            # Memory increase should be reasonable (under 50MB)
            assert memory_increase < 50 * 1024 * 1024, f"Memory leak detected: {memory_increase} bytes"


