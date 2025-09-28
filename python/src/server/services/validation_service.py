"""
Input Validation and Sanitization Service for Zippy Archon

Provides comprehensive data validation, sanitization, and security checks
to prevent injection attacks and ensure data integrity.
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from urllib.parse import urlparse

from .error_service import error_service


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    sanitized_value: Any = None

    def __bool__(self) -> bool:
        return self.is_valid

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)

    def set_value(self, value: Any):
        """Set the sanitized value."""
        self.sanitized_value = value


@dataclass
class ValidationRule:
    """Configuration for a validation rule."""
    name: str
    validator: Callable[[Any], ValidationResult]
    required: bool = True
    description: str = ""


class ValidationService:
    """Comprehensive input validation and sanitization service."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Common validation patterns
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'url': re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE),
            'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
            'slug': re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE),
            'phone': re.compile(r'^\+?[\d\s\-\(\)]+$'),
            'sql_injection': re.compile(r'(\b(union|select|insert|delete|update|drop|create|alter|exec|execute)\b)', re.IGNORECASE),
            'script_tags': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            'html_tags': re.compile(r'<[^>]+>'),
        }

        # Content type validation rules
        self.content_type_limits = {
            'text': {'max_length': 10000, 'encoding': 'utf-8'},
            'description': {'max_length': 5000, 'encoding': 'utf-8'},
            'title': {'max_length': 200, 'encoding': 'utf-8'},
            'name': {'max_length': 100, 'encoding': 'utf-8'},
            'email': {'max_length': 254, 'encoding': 'utf-8'},
            'url': {'max_length': 2000, 'encoding': 'utf-8'},
            'tag': {'max_length': 50, 'encoding': 'utf-8'},
            'filename': {'max_length': 255, 'encoding': 'utf-8'},
        }

    def validate_string(
        self,
        value: Any,
        field_name: str = "value",
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        required: bool = True
    ) -> ValidationResult:
        """Validate a string value with comprehensive checks."""

        result = ValidationResult(is_valid=True, errors=[])

        # Check if required
        if required and (value is None or str(value).strip() == ""):
            result.add_error(f"{field_name} is required")
            result.is_valid = False
            return result

        # Convert to string if not None
        if value is not None:
            value = str(value)

            # Length validation
            if min_length and len(value) < min_length:
                result.add_error(f"{field_name} must be at least {min_length} characters long")

            if max_length and len(value) > max_length:
                result.add_error(f"{field_name} must not exceed {max_length} characters")

            # Pattern validation
            if pattern and not re.match(pattern, value):
                result.add_error(f"{field_name} format is invalid")

            # Security checks
            if self.patterns['sql_injection'].search(value):
                result.add_error(f"{field_name} contains potentially dangerous SQL patterns")

            if self.patterns['script_tags'].search(value):
                result.add_error(f"{field_name} contains script tags which are not allowed")

            # Sanitize the value
            sanitized = self.sanitize_string(value)
            result.set_value(sanitized)

        if result.errors:
            result.is_valid = False

        return result

    def validate_email(self, email: str, field_name: str = "email", required: bool = True) -> ValidationResult:
        """Validate an email address."""

        result = self.validate_string(
            email,
            field_name=field_name,
            max_length=self.content_type_limits['email']['max_length'],
            required=required
        )

        if result.is_valid and email:
            if not self.patterns['email'].match(email):
                result.add_error(f"{field_name} must be a valid email address")
                result.is_valid = False

        return result

    def validate_url(self, url: str, field_name: str = "url", required: bool = True) -> ValidationResult:
        """Validate a URL."""

        result = self.validate_string(
            url,
            field_name=field_name,
            max_length=self.content_type_limits['url']['max_length'],
            required=required
        )

        if result.is_valid and url:
            # Basic URL pattern check
            if not self.patterns['url'].match(url):
                result.add_error(f"{field_name} must be a valid URL")
                result.is_valid = False
                return result

            # Additional URL validation
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    result.add_error(f"{field_name} must include scheme (http/https) and domain")
                    result.is_valid = False
            except Exception:
                result.add_error(f"{field_name} is not a valid URL format")
                result.is_valid = False

        return result

    def validate_project_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate project creation/update data."""

        result = ValidationResult(is_valid=True, errors=[])

        # Title validation
        title_result = self.validate_string(
            data.get('title'),
            field_name="title",
            min_length=1,
            max_length=self.content_type_limits['title']['max_length']
        )
        if not title_result:
            result.errors.extend(title_result.errors)
            result.is_valid = False

        # Description validation (optional)
        if 'description' in data:
            desc_result = self.validate_string(
                data.get('description'),
                field_name="description",
                max_length=self.content_type_limits['description']['max_length'],
                required=False
            )
            if not desc_result:
                result.errors.extend(desc_result.errors)
                result.is_valid = False

        # GitHub repo validation (optional)
        if 'github_repo' in data and data.get('github_repo'):
            repo_result = self.validate_url(
                data.get('github_repo'),
                field_name="github_repo",
                required=False
            )
            if not repo_result:
                result.errors.extend(repo_result.errors)
                result.is_valid = False

        # Source IDs validation
        for source_type in ['technical_sources', 'business_sources']:
            if source_type in data and data.get(source_type):
                sources = data.get(source_type)
                if isinstance(sources, list):
                    for i, source_id in enumerate(sources):
                        if not isinstance(source_id, str) or not source_id.strip():
                            result.add_error(f"{source_type}[{i}] must be a non-empty string")
                            result.is_valid = False
                else:
                    result.add_error(f"{source_type} must be a list of strings")
                    result.is_valid = False

        return result

    def validate_task_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate task creation/update data."""

        result = ValidationResult(is_valid=True, errors=[])

        # Required fields
        title_result = self.validate_string(
            data.get('title'),
            field_name="title",
            min_length=1,
            max_length=self.content_type_limits['title']['max_length']
        )
        if not title_result:
            result.errors.extend(title_result.errors)
            result.is_valid = False

        # Project ID validation
        if not data.get('project_id') or not isinstance(data.get('project_id'), str):
            result.add_error("project_id is required and must be a string")
            result.is_valid = False

        # Optional fields
        if 'description' in data:
            desc_result = self.validate_string(
                data.get('description'),
                field_name="description",
                max_length=self.content_type_limits['description']['max_length'],
                required=False
            )
            if not desc_result:
                result.errors.extend(desc_result.errors)
                result.is_valid = False

        # Status validation
        valid_statuses = ['todo', 'in_progress', 'review', 'done']
        if 'status' in data and data.get('status') not in valid_statuses:
            result.add_error(f"status must be one of: {', '.join(valid_statuses)}")
            result.is_valid = False

        return result

    def validate_knowledge_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate knowledge item data."""

        result = ValidationResult(is_valid=True, errors=[])

        # Required fields
        title_result = self.validate_string(
            data.get('title'),
            field_name="title",
            min_length=1,
            max_length=self.content_type_limits['title']['max_length']
        )
        if not title_result:
            result.errors.extend(title_result.errors)
            result.is_valid = False

        content_result = self.validate_string(
            data.get('content'),
            field_name="content",
            max_length=self.content_type_limits['text']['max_length']
        )
        if not content_result:
            result.errors.extend(content_result.errors)
            result.is_valid = False

        # Content type validation
        valid_types = ['document', 'code', 'tutorial', 'reference', 'note']
        if 'content_type' in data and data.get('content_type') not in valid_types:
            result.add_error(f"content_type must be one of: {', '.join(valid_types)}")
            result.is_valid = False

        # URL validation (optional)
        if 'source_url' in data and data.get('source_url'):
            url_result = self.validate_url(
                data.get('source_url'),
                field_name="source_url",
                required=False
            )
            if not url_result:
                result.errors.extend(url_result.errors)
                result.is_valid = False

        return result

    def validate_file_upload(self, file, allowed_types: Optional[List[str]] = None) -> ValidationResult:
        """Validate uploaded file for security and type."""

        result = ValidationResult(is_valid=True, errors=[])

        if not hasattr(file, 'filename'):
            result.add_error("Invalid file object")
            result.is_valid = False
            return result

        filename = file.filename

        # Filename validation
        if not filename or len(filename) > self.content_type_limits['filename']['max_length']:
            result.add_error("Invalid filename or filename too long")
            result.is_valid = False

        # File extension validation
        if allowed_types:
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if file_ext not in [t.lower() for t in allowed_types]:
                result.add_error(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
                result.is_valid = False

        # Dangerous filename patterns
        dangerous_patterns = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        if any(pattern in filename for pattern in dangerous_patterns):
            result.add_error("Filename contains dangerous characters")
            result.is_valid = False

        # File size validation (if available)
        if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:  # 10MB limit
            result.add_error("File size exceeds 10MB limit")
            result.is_valid = False

        return result

    def sanitize_string(self, value: str) -> str:
        """Sanitize a string value for safe storage/display."""

        if not isinstance(value, str):
            return str(value)

        # HTML escape
        sanitized = html.escape(value)

        # Remove or encode potentially dangerous characters
        # Allow basic punctuation but remove control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

        # Trim whitespace
        sanitized = sanitized.strip()

        return sanitized

    def sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content to prevent XSS attacks."""

        if not isinstance(html_content, str):
            return ""

        # Use a more sophisticated HTML sanitizer if available
        # For now, we'll use a basic approach
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove dangerous tags
            dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed']
            for tag in dangerous_tags:
                for element in soup.find_all(tag):
                    element.decompose()

            # Remove dangerous attributes
            dangerous_attrs = ['onclick', 'onload', 'onerror', 'javascript:', 'data:']
            for tag in soup.find_all():
                for attr in list(tag.attrs):
                    if any(dangerous in str(tag.attrs[attr]).lower() for dangerous in dangerous_attrs):
                        del tag.attrs[attr]

            return str(soup)

        except Exception as e:
            self.logger.warning(f"HTML sanitization failed: {e}")
            # Fallback to basic text escaping
            return self.sanitize_string(html_content)

    def validate_request_data(self, data: Dict[str, Any], schema: Dict[str, ValidationRule]) -> ValidationResult:
        """Validate request data against a validation schema."""

        result = ValidationResult(is_valid=True, errors=[])
        validated_data = {}

        for field_name, rule in schema.items():
            field_value = data.get(field_name)

            # Run the validation function
            field_result = rule.validator(field_value)

            if not field_result:
                result.errors.extend([f"{field_name}: {error}" for error in field_result.errors])
                result.is_valid = False
            elif field_result.sanitized_value is not None:
                validated_data[field_name] = field_result.sanitized_value
            else:
                validated_data[field_name] = field_value

        if result.is_valid:
            result.set_value(validated_data)

        return result

    def log_validation_error(self, field_name: str, errors: List[str], request_context: Optional[Dict] = None):
        """Log validation errors for monitoring."""

        error_msg = f"Validation failed for {field_name}: {', '.join(errors)}"

        if request_context:
            error_msg += f" - Context: {request_context}"

        self.logger.warning(error_msg)

        # Could also send to monitoring service
        # monitoring_service.log_validation_error(field_name, errors, request_context)


# Global validation service instance
validation_service = ValidationService()

# Convenience functions for common validations
def validate_project_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate project data."""
    return validation_service.validate_project_data(data)

def validate_task_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate task data."""
    return validation_service.validate_task_data(data)

def validate_knowledge_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate knowledge data."""
    return validation_service.validate_knowledge_data(data)

def sanitize_string(value: str) -> str:
    """Sanitize a string value."""
    return validation_service.sanitize_string(value)

def validate_file_upload(file, allowed_types: Optional[List[str]] = None) -> ValidationResult:
    """Validate uploaded file."""
    return validation_service.validate_file_upload(file, allowed_types)
