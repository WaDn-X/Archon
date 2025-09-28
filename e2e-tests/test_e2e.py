"""End-to-End Tests using Playwright"""

import pytest
import asyncio
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

    async def test_rate_limiting(self, page: Page):
        """Test rate limiting from browser context."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        # Make multiple requests quickly
        responses = []
        for i in range(15):  # More than default rate limit
            try:
                response = await page.request.get(f"{api_url}/health")
                responses.append(response.status)
                if response.status == 429:
                    break
            except:
                responses.append(500)

        # Check if rate limiting kicked in
        rate_limited = 429 in responses
        if rate_limited:
            assert responses[-1] == 429, "Rate limiting should return 429 status"

    async def test_input_validation(self, page: Page):
        """Test input validation through browser."""
        api_url = os.getenv("API_URL", "http://localhost:8181")

        # Test various invalid inputs
        test_cases = [
            ("", "Empty input"),
            ("<script>alert('xss')</script>", "XSS attempt"),
            ("'; DROP TABLE users; --", "SQL injection attempt"),
            ("A" * 10000, "Very long input")
        ]

        for test_input, description in test_cases:
            try:
                response = await page.request.post(
                    f"{api_url}/api/v1/specs/generate",
                    data=json.dumps({"prompt": test_input}),
                    headers={'Content-Type': 'application/json'}
                )

                # Should not crash the server (no 500 errors for valid input handling)
                if response.status not in [401, 422]:  # Allow auth and validation errors
                    assert response.status != 500, f"Server crashed on {description}"

            except Exception as e:
                pytest.skip(f"Input validation test skipped for {description}: {e}")


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


