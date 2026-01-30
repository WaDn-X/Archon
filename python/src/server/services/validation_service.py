"""
Input Validation and Sanitization Service for Zippy Archon

Provides comprehensive data validation, sanitization, and security checks
to prevent injection attacks and ensure data integrity.
"""

import re
import html
import logging
import bleach
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from urllib.parse import urlparse
import ipaddress
from email_validator import validate_email, EmailNotValidError

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

    # Enhanced security validation methods
    def validate_email_address(self, email: str) -> ValidationResult:
        """Validate email address with enhanced security checks."""
        result = ValidationResult(is_valid=True, errors=[])

        if not email or not isinstance(email, str):
            result.add_error("Email is required and must be a string")
            result.is_valid = False
            return result

        email = email.strip().lower()

        if len(email) > 254:  # RFC 5321 limit
            result.add_error("Email address is too long")
            result.is_valid = False
            return result

        try:
            # Use email_validator for comprehensive validation
            valid = validate_email(email, check_deliverability=False)
            result.set_value(valid.email)
        except EmailNotValidError as e:
            result.add_error(f"Invalid email address: {str(e)}")
            result.is_valid = False

        return result

    def validate_password_strength(self, password: str) -> ValidationResult:
        """Validate password strength with security requirements."""
        result = ValidationResult(is_valid=True, errors=[])

        if not password or not isinstance(password, str):
            result.add_error("Password is required")
            result.is_valid = False
            return result

        # Length requirements
        if len(password) < 8:
            result.add_error("Password must be at least 8 characters long")
            result.is_valid = False

        if len(password) > 128:
            result.add_error("Password must be less than 128 characters long")
            result.is_valid = False

        # Complexity requirements
        if not re.search(r'[A-Z]', password):
            result.add_error("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', password):
            result.add_error("Password must contain at least one lowercase letter")

        if not re.search(r'\d', password):
            result.add_error("Password must contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result.add_error("Password must contain at least one special character")

        # Check for common weak patterns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123',
            r'admin', r'user', r'login'
        ]

        for pattern in common_patterns:
            if pattern in password.lower():
                result.add_error("Password contains common weak pattern")
                result.is_valid = False
                break

        return result

    def validate_url_security(self, url: str, allowed_domains: Optional[List[str]] = None) -> ValidationResult:
        """Validate URL for security and allowed domains."""
        result = ValidationResult(is_valid=True, errors=[])

        if not url or not isinstance(url, str):
            result.add_error("URL is required and must be a string")
            result.is_valid = False
            return result

        url = url.strip()

        try:
            parsed = urlparse(url)

            # Must have scheme
            if not parsed.scheme:
                result.add_error("URL must include a scheme (http:// or https://)")
                result.is_valid = False

            # Must be HTTP or HTTPS
            if parsed.scheme not in ['http', 'https']:
                result.add_error("URL must use HTTP or HTTPS protocol")
                result.is_valid = False

            # Check for suspicious patterns
            suspicious_patterns = [
                r'\.\.',  # Double dots
                r'localhost',
                r'127\.0\.0\.1',
                r'0\.0\.0\.0',
                r'169\.254\.',  # Link-local
                r'10\.0\.0\.0/8',  # Private network
                r'172\.16\.0\.0/12',  # Private network
                r'192\.168\.0\.0/16',  # Private network
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    result.add_error(f"URL contains suspicious pattern: {pattern}")
                    result.is_valid = False
                    break

            # Check allowed domains if specified
            if allowed_domains and parsed.netloc:
                domain_allowed = False
                for allowed_domain in allowed_domains:
                    if parsed.netloc == allowed_domain or parsed.netloc.endswith('.' + allowed_domain):
                        domain_allowed = True
                        break

                if not domain_allowed:
                    result.add_error(f"Domain {parsed.netloc} is not in allowed domains list")
                    result.is_valid = False

        except Exception as e:
            result.add_error(f"Invalid URL format: {str(e)}")
            result.is_valid = False

        if result.is_valid:
            result.set_value(url)

        return result

    def validate_file_upload(self, filename: str, content_type: str, file_size: int) -> ValidationResult:
        """Validate file upload for security."""
        result = ValidationResult(is_valid=True, errors=[])

        # File size limits (10MB default)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            result.add_error(f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes")
            result.is_valid = False

        # Allowed file extensions
        allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.md'],
            'archive': ['.zip', '.tar.gz', '.tar.bz2'],
            'code': ['.py', '.js', '.ts', '.json', '.yaml', '.yml']
        }

        # Allowed MIME types
        allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/zip', 'application/x-tar', 'application/json',
            'text/markdown', 'application/x-yaml'
        }

        # Extract file extension
        if '.' in filename:
            extension = '.' + filename.split('.')[-1].lower()

            # Check if extension is allowed for any category
            extension_allowed = any(extension in extensions for extensions in allowed_extensions.values())
            if not extension_allowed:
                result.add_error(f"File extension {extension} is not allowed")
                result.is_valid = False

        # Validate MIME type
        if content_type not in allowed_mime_types:
            result.add_error(f"MIME type {content_type} is not allowed")
            result.is_valid = False

        # Check for suspicious filenames
        suspicious_names = [
            'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
            'lpt1', 'lpt2', 'lpt3', 'lpt4'
        ]

        base_name = filename.split('.')[0].lower() if '.' in filename else filename.lower()
        if base_name in suspicious_names:
            result.add_error(f"Filename {filename} is not allowed (reserved system name)")
            result.is_valid = False

        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            result.add_error("Filename contains invalid path characters")
            result.is_valid = False

        return result

    def validate_ip_address(self, ip_str: str) -> ValidationResult:
        """Validate IP address format and security."""
        result = ValidationResult(is_valid=True, errors=[])

        try:
            ip = ipaddress.ip_address(ip_str)

            # Check for private/reserved addresses that shouldn't be allowed
            if ip.is_private:
                result.add_error("Private IP addresses are not allowed")
                result.is_valid = False
            elif ip.is_loopback:
                result.add_error("Loopback addresses are not allowed")
                result.is_valid = False
            elif ip.is_link_local:
                result.add_error("Link-local addresses are not allowed")
                result.is_valid = False
            elif ip.is_reserved:
                result.add_error("Reserved IP addresses are not allowed")
                result.is_valid = False

            result.set_value(str(ip))

        except ValueError as e:
            result.add_error(f"Invalid IP address format: {str(e)}")
            result.is_valid = False

        return result

    def sanitize_html_content(self, html_content: str, allowed_tags: Optional[List[str]] = None) -> ValidationResult:
        """Sanitize HTML content for security."""
        result = ValidationResult(is_valid=True, errors=[])

        if not html_content or not isinstance(html_content, str):
            result.set_value("")
            return result

        # Default allowed tags for rich text content
        if allowed_tags is None:
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img'
            ]

        allowed_attrs = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title']
        }

        try:
            # Use bleach for comprehensive HTML sanitization
            sanitized = bleach.clean(
                html_content,
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )

            # Additional security checks
            if len(sanitized) > 10000:  # 10KB limit for HTML content
                result.add_error("HTML content is too long after sanitization")
                result.is_valid = False
            else:
                result.set_value(sanitized)

        except Exception as e:
            result.add_error(f"HTML sanitization failed: {str(e)}")
            result.is_valid = False
            # Fallback to text-only sanitization
            result.set_value(self.sanitize_string(html_content))

        return result


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
