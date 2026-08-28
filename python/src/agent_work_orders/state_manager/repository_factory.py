"""Repository Factory

Creates appropriate repository instances based on configuration.
Supports in-memory (dev/testing) and file-based (production) storage.
"""

from ..config import config
from ..utils.structured_logger import get_logger
from .file_state_repository import FileStateRepository
from .work_order_repository import WorkOrderRepository

logger = get_logger(__name__)

# Supported storage types
SUPPORTED_STORAGE_TYPES = ["memory", "file"]


def create_repository() -> WorkOrderRepository | FileStateRepository:
    """Create a work order repository based on configuration

    Returns:
        Repository instance (in-memory or file-based)

    Raises:
        ValueError: If storage_type is invalid
    """
    storage_type = config.STATE_STORAGE_TYPE.lower()

    if storage_type == "file":
        state_dir = config.FILE_STATE_DIRECTORY
        logger.info(
            "repository_created",
            storage_type="file",
            state_directory=state_dir
        )
        return FileStateRepository(state_dir)
    elif storage_type == "memory":
        logger.info(
            "repository_created",
            storage_type="memory"
        )
        return WorkOrderRepository()
    else:
        error_msg = (
            f"Invalid storage type '{storage_type}'. "
            f"Supported types are: {', '.join(SUPPORTED_STORAGE_TYPES)}"
        )
        logger.error(
            "invalid_storage_type",
            storage_type=storage_type,
            supported_types=SUPPORTED_STORAGE_TYPES,
        )
        raise ValueError(error_msg)
