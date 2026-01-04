"""
Service Factory Module

Provides factory functions that return the appropriate service implementation
based on the STORAGE_BACKEND environment variable.

Usage:
    from .service_factory import get_project_service, get_task_service

    # Get service based on STORAGE_BACKEND env var
    project_service = get_project_service()

Environment Variables:
    STORAGE_BACKEND: "vespa" (default)
    EMBEDDING_PROVIDER: "openai" (default), "voyage", "cohere", or "echo"
"""

import os
from typing import TYPE_CHECKING

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

# Type hints for IDE support
if TYPE_CHECKING:
    from .vespa_project_service import VespaProjectService
    from .vespa_task_service import VespaTaskService


def get_storage_backend() -> str:
    """
    Get the configured storage backend.

    Returns:
        "vespa"
    """
    backend = os.getenv("STORAGE_BACKEND", "vespa").lower()
    if backend != "vespa":
        logger.warning(f"Invalid STORAGE_BACKEND '{backend}', defaulting to 'vespa'")
        return "vespa"
    return backend


def get_project_service():
    """
    Get the project service based on STORAGE_BACKEND configuration.

    Returns:
        VespaProjectService instance
    """
    logger.info("Using Vespa backend for ProjectService")
    from .vespa_project_service import VespaProjectService
    return VespaProjectService()


def get_task_service():
    """
    Get the task service based on STORAGE_BACKEND configuration.

    Returns:
        VespaTaskService instance
    """
    logger.info("Using Vespa backend for TaskService")
    from .vespa_task_service import VespaTaskService
    return VespaTaskService()


def is_vespa_enabled() -> bool:
    """
    Check if Vespa backend is enabled.

    Returns:
        True (always, as Vespa is the only supported backend)
    """
    return True


def get_backend_info() -> dict:
    """
    Get information about the current storage backend configuration.

    Returns:
        Dict with backend info for health checks and debugging
    """
    return {
        "storage_backend": "vespa",
        "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "openai"),
        "vespa_host": os.getenv("VESPA_HOST", "localhost"),
        "vespa_port": os.getenv("VESPA_PORT", "8081"),
    }
