"""Execute allowlist for plugins and sandbox executors.

Extra Python plugins and non-first-party executors must be explicitly
allowlisted by name and SHA-256 hash before they can load or run.
"""

from .exceptions import AllowlistError, ExecutorNotAllowedError, PluginNotAllowedError
from .executors import FIRST_PARTY_EXECUTORS, validate_sandbox_command
from .loader import load_allowed_plugin, load_allowlisted_plugins_from_directory
from .models import AllowlistEntry, AllowlistFile
from .service import AllowlistService, get_allowlist_service

__all__ = [
    "AllowlistEntry",
    "AllowlistError",
    "AllowlistFile",
    "AllowlistService",
    "ExecutorNotAllowedError",
    "FIRST_PARTY_EXECUTORS",
    "PluginNotAllowedError",
    "get_allowlist_service",
    "load_allowed_plugin",
    "load_allowlisted_plugins_from_directory",
    "validate_sandbox_command",
]
