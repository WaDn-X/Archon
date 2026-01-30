"""
Authentication and Security Middleware for FastAPI

Provides comprehensive security middleware including:
- JWT token validation
- API key authentication
- Rate limiting
- Request logging and monitoring
- Security headers
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError

from ..services.auth_service import auth_service, User
from ..services.error_service import error_service


class AuthMiddleware:
    """Enhanced authentication middleware for request processing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process authentication for each request."""

        # Skip authentication for health checks and public endpoints
        public_paths = ["/health", "/api/health", "/", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_paths:
            return await call_next(request)

        # Try to authenticate user with enhanced methods
        user = await self._authenticate_user(request)

        # Check for token refresh if authentication failed
        if not user:
            user = await self._try_token_refresh(request)

        # Add user info to request state for use in handlers
        request.state.user = user

        # Log authentication attempt
        if user:
            self.logger.info(f"Authenticated request: {user.user_id} - {request.method} {request.url.path}")
        else:
            self.logger.warning(f"Unauthenticated request: {request.method} {request.url.path}")

        # Process the request
        response = await call_next(request)

        return response

    async def _authenticate_user(self, request: Request) -> Optional[User]:
        """Enhanced user authentication with multiple methods."""
        # Try Bearer token first
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]

            # Basic token validation
            if not token or len(token) < 10:
                self.logger.warning("Invalid Bearer token format received")
                return None

            try:
                token_data = auth_service.verify_token(token)
                if token_data:
                    return User(
                        user_id=token_data.user_id,
                        role=token_data.role
                    )
            except JWTError as e:
                self.logger.warning(f"JWT verification failed: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error during token verification: {e}")
                return None

        # Try API key
        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if api_key:
            user = await auth_service.authenticate_api_key(api_key)
            if user:
                return user

        # Try session cookie
        session_token = request.cookies.get("session_token")
        if session_token:
            token_data = auth_service.verify_token(session_token)
            if token_data:
                return User(
                    user_id=token_data.user_id,
                    role=token_data.role
                )

        return None

    async def _try_token_refresh(self, request: Request) -> Optional[User]:
        """Attempt to refresh access token using refresh token."""
        # Check for refresh token in cookies or headers
        refresh_token = (
            request.cookies.get("refresh_token") or
            request.headers.get("x-refresh-token")
        )

        if refresh_token:
            try:
                # Try to get new access token
                new_access_token = auth_service.refresh_access_token(refresh_token)
                if new_access_token:
                    # Verify the new token and return user
                    token_data = auth_service.verify_token(new_access_token)
                    if token_data:
                        self.logger.info(f"Token refreshed for user: {token_data.user_id}")
                        return User(
                            user_id=token_data.user_id,
                            role=token_data.role
                        )
            except Exception as e:
                self.logger.warning(f"Token refresh failed: {e}")

        return None


class RateLimitMiddleware:
    """Rate limiting middleware with user-based and IP-based limits."""

    def __init__(self):
        self.limiter = Limiter(key_func=self._get_rate_limit_key)
        self.logger = logging.getLogger(__name__)

        # Rate limits by endpoint type
        self.rate_limits = {
            "auth": "10/minute",  # Authentication endpoints
            "api": "100/minute",  # General API endpoints
            "search": "50/minute",  # Search endpoints
            "admin": "20/minute",  # Admin endpoints
        }

    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key based on user or IP."""
        user = getattr(request.state, 'user', None)
        if user:
            return f"user:{user.user_id}:{request.url.path}"
        else:
            return f"ip:{get_remote_address(request)}:{request.url.path}"

    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting."""
        if any(keyword in path for keyword in ["/auth", "/login", "/register"]):
            return "auth"
        elif any(keyword in path for keyword in ["/admin", "/manage", "/system"]):
            return "admin"
        elif any(keyword in path for keyword in ["/search", "/query"]):
            return "search"
        else:
            return "api"

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)

        try:
            # Determine rate limit for this endpoint
            endpoint_type = self._get_endpoint_type(request.url.path)
            rate_limit = self.rate_limits.get(endpoint_type, "100/minute")

            # Apply rate limiting
            @self.limiter.limit(rate_limit)
            async def rate_limited_request():
                return await call_next(request)

            return await rate_limited_request()

        except RateLimitExceeded:
            self.logger.warning(f"Rate limit exceeded for {request.method} {request.url.path}")

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60  # seconds
                    }
                },
                headers={"Retry-After": "60"}
            )


class SecurityHeadersMiddleware:
    """Middleware to add comprehensive security headers."""

    def __init__(self):
        self.security_headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # XSS protection
            "X-XSS-Protection": "1; mode=block",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Content Security Policy (basic)
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",

            # HSTS (HTTP Strict Transport Security)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",

            # Permissions Policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",

            # Server identification (remove or customize)
            "Server": "Zippy-Archon/1.0",

            # Feature Policy (deprecated but still useful)
            "Feature-Policy": "geolocation 'none'; microphone 'none'; camera 'none'",
        }

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to all responses."""
        response = await call_next(request)

        # Add all security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        return response


class RequestLoggingMiddleware:
    """Comprehensive request logging middleware."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Log all requests with performance metrics."""
        start_time = time.time()

        # Log incoming request
        user = getattr(request.state, 'user', None)
        user_id = user.user_id if user else "anonymous"

        self.logger.info(
            f"REQUEST: {request.method} {request.url.path} "
            f"- User: {user_id} "
            f"- IP: {get_remote_address(request)} "
            f"- User-Agent: {request.headers.get('user-agent', 'Unknown')}"
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            self.logger.info(
                f"RESPONSE: {request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Time: {process_time:.3f}s "
                f"- User: {user_id}"
            )

            # Add processing time to response headers
            response.headers["X-Process-Time"] = ".3f"

            # Alert on slow requests
            if process_time > 2.0:  # 2 seconds
                self.logger.warning(
                    f"SLOW REQUEST: {request.method} {request.url.path} "
                    f"took {process_time:.3f}s"
                )

            return response

        except Exception as e:
            # Log errors
            process_time = time.time() - start_time
            self.logger.error(
                f"ERROR: {request.method} {request.url.path} "
                f"- Error: {str(e)} "
                f"- Time: {process_time:.3f}s "
                f"- User: {user_id}"
            )
            raise


class ErrorHandlingMiddleware:
    """Global error handling and standardization middleware."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Handle and standardize all errors."""
        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return error_service.create_error_response(
                request=request,
                error_code=self._map_http_status_to_error_code(e.status_code),
                message=e.detail,
                status_code=e.status_code
            )

        except RateLimitExceeded:
            # Handle rate limiting errors
            return error_service.create_error_response(
                request=request,
                error_code="RATE_LIMIT_EXCEEDED",
                message="Too many requests. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)

            return error_service.create_error_response(
                request=request,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                include_trace=request.app.debug if hasattr(request.app, 'debug') else False
            )

    def _map_http_status_to_error_code(self, status_code: int) -> str:
        """Map HTTP status codes to error codes."""
        mapping = {
            400: "VALIDATION_ERROR",
            401: "AUTHENTICATION_ERROR",
            403: "AUTHORIZATION_ERROR",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_ERROR",
            500: "INTERNAL_ERROR",
        }
        return mapping.get(status_code, "UNKNOWN_ERROR")


# Global middleware instances
auth_middleware = AuthMiddleware()
rate_limit_middleware = RateLimitMiddleware()
security_headers_middleware = SecurityHeadersMiddleware()
request_logging_middleware = RequestLoggingMiddleware()
error_handling_middleware = ErrorHandlingMiddleware()
