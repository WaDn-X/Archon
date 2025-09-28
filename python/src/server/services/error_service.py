"""
Error Service for standardized error handling and responses

Provides consistent error formatting, logging, and user-friendly messages
across the entire Zippy Archon platform.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from fastapi import Request, status
from fastapi.responses import JSONResponse


@dataclass
class ErrorResponse:
    """Standardized error response structure."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    path: str = ""
    request_id: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


class ErrorService:
    """Centralized error handling service."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Error code mappings
        self.error_codes = {
            # Authentication errors
            "AUTHENTICATION_ERROR": {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "user_message": "Authentication required. Please log in.",
                "log_level": "warning"
            },
            "AUTHORIZATION_ERROR": {
                "status_code": status.HTTP_403_FORBIDDEN,
                "user_message": "You don't have permission to perform this action.",
                "log_level": "warning"
            },
            "INVALID_TOKEN": {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "user_message": "Your session has expired. Please log in again.",
                "log_level": "info"
            },

            # Validation errors
            "VALIDATION_ERROR": {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "user_message": "The provided data is invalid. Please check your input.",
                "log_level": "info"
            },
            "MISSING_REQUIRED_FIELD": {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "user_message": "Required information is missing. Please provide all necessary details.",
                "log_level": "info"
            },

            # Resource errors
            "NOT_FOUND": {
                "status_code": status.HTTP_404_NOT_FOUND,
                "user_message": "The requested resource was not found.",
                "log_level": "info"
            },
            "CONFLICT": {
                "status_code": status.HTTP_409_CONFLICT,
                "user_message": "This action conflicts with existing data.",
                "log_level": "warning"
            },
            "ALREADY_EXISTS": {
                "status_code": status.HTTP_409_CONFLICT,
                "user_message": "This item already exists.",
                "log_level": "info"
            },

            # Rate limiting
            "RATE_LIMIT_ERROR": {
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "user_message": "Too many requests. Please wait a moment before trying again.",
                "log_level": "warning"
            },
            "RATE_LIMIT_EXCEEDED": {
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "user_message": "You've made too many requests. Please try again later.",
                "log_level": "warning"
            },

            # System errors
            "INTERNAL_ERROR": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "user_message": "Something went wrong on our end. Please try again later.",
                "log_level": "error"
            },
            "SERVICE_UNAVAILABLE": {
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "user_message": "Service is temporarily unavailable. Please try again later.",
                "log_level": "error"
            },
            "DATABASE_ERROR": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "user_message": "Database temporarily unavailable. Please try again.",
                "log_level": "error"
            },

            # External service errors
            "EXTERNAL_SERVICE_ERROR": {
                "status_code": status.HTTP_502_BAD_GATEWAY,
                "user_message": "External service is currently unavailable.",
                "log_level": "error"
            },
            "AI_SERVICE_ERROR": {
                "status_code": status.HTTP_502_BAD_GATEWAY,
                "user_message": "AI service is temporarily unavailable. Please try again.",
                "log_level": "warning"
            },

            # File upload errors
            "FILE_TOO_LARGE": {
                "status_code": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "user_message": "File is too large. Please choose a smaller file.",
                "log_level": "info"
            },
            "INVALID_FILE_TYPE": {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "user_message": "File type not supported. Please choose a different file.",
                "log_level": "info"
            },
            "UPLOAD_FAILED": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "user_message": "File upload failed. Please try again.",
                "log_level": "error"
            }
        }

    def create_error_response(
        self,
        request: Request,
        error_code: str,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        include_trace: bool = False
    ) -> JSONResponse:
        """Create standardized error response."""

        # Get error configuration
        error_config = self.error_codes.get(error_code, self.error_codes["INTERNAL_ERROR"])

        # Use provided status code or default from config
        final_status_code = status_code or error_config["status_code"]

        # Use provided message or default user message
        final_message = message or error_config["user_message"]

        # Log the error
        log_level = error_config["log_level"]
        log_message = f"Error {error_code}: {final_message}"

        if details:
            log_message += f" - Details: {details}"

        if request:
            log_message += f" - Path: {request.url.path}"

        getattr(self.logger, log_level)(log_message)

        # Create error response
        error_response = ErrorResponse(
            error_code=error_code,
            message=final_message,
            details=details,
            path=str(request.url.path) if request else "",
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        # Add stack trace in debug mode
        if include_trace:
            error_response.details = error_response.details or {}
            error_response.details["traceback"] = traceback.format_exc()

        return JSONResponse(
            status_code=final_status_code,
            content=error_response.dict()
        )

    def handle_validation_error(self, request: Request, errors: Dict[str, Any]) -> JSONResponse:
        """Handle Pydantic validation errors."""
        details = {
            "validation_errors": errors,
            "field_count": len(errors)
        }

        return self.create_error_response(
            request=request,
            error_code="VALIDATION_ERROR",
            message="Please correct the highlighted fields and try again.",
            details=details
        )

    def handle_database_error(self, request: Request, operation: str, error: Exception) -> JSONResponse:
        """Handle database-related errors."""
        self.logger.error(f"Database error during {operation}: {str(error)}")

        return self.create_error_response(
            request=request,
            error_code="DATABASE_ERROR",
            message="Database operation failed. Please try again.",
            details={"operation": operation}
        )

    def handle_external_service_error(
        self,
        request: Request,
        service_name: str,
        error: Exception
    ) -> JSONResponse:
        """Handle external service errors."""
        self.logger.error(f"External service error ({service_name}): {str(error)}")

        return self.create_error_response(
            request=request,
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service_name} is currently unavailable. Please try again later.",
            details={"service": service_name}
        )

    def handle_rate_limit_error(self, request: Request, retry_after: int = 60) -> JSONResponse:
        """Handle rate limiting errors."""
        return self.create_error_response(
            request=request,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )

    def log_error(
        self,
        error_code: str,
        message: str,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ):
        """Log an error without creating a response."""
        error_config = self.error_codes.get(error_code, self.error_codes["INTERNAL_ERROR"])
        log_level = error_config["log_level"]

        log_message = f"Error {error_code}: {message}"

        if details:
            log_message += f" - Details: {details}"

        if request:
            log_message += f" - Path: {request.url.path}"

        getattr(self.logger, log_level)(log_message, exc_info=exc_info)

    def get_error_codes(self) -> Dict[str, Dict[str, Any]]:
        """Get all available error codes and their configurations."""
        return self.error_codes.copy()


# Global error service instance
error_service = ErrorService()
