"""Secure plugin loading via the execute allowlist."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from .exceptions import PluginNotAllowedError
from .service import get_allowlist_service

logger = logging.getLogger(__name__)


def load_allowed_plugin(path: str | Path, *, name: str | None = None) -> ModuleType:
    """Load a Python plugin only after allowlist verification.

    The file is hashed and checked against the allowlist before importlib runs.
    """
    plugin_path = Path(path).resolve()
    service = get_allowlist_service()
    entry = service.verify_plugin(plugin_path, expected_name=name)
    module_name = f"archon_allowlisted_plugin.{entry.name}"

    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
    if spec is None or spec.loader is None:
        raise PluginNotAllowedError(f"Could not create import spec for plugin: {plugin_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    logger.info("Loaded allowlisted plugin %s from %s", entry.name, plugin_path)
    return module


def load_allowlisted_plugins_from_directory(
    plugin_dir: str | Path,
    *,
    register_callback: Any | None = None,
) -> list[ModuleType]:
    """Load every allowlisted plugin module found in a directory.

    Args:
        plugin_dir: Directory containing plugin ``.py`` files.
        register_callback: Optional callable invoked as ``register_callback(module)``
            after each plugin is loaded.

    Returns:
        List of successfully loaded plugin modules. Non-allowlisted files are skipped.
    """
    directory = Path(plugin_dir)
    if not directory.is_dir():
        return []

    loaded: list[ModuleType] = []
    for plugin_path in sorted(directory.glob("*.py")):
        if plugin_path.name.startswith("_"):
            continue

        try:
            module = load_allowed_plugin(plugin_path)
        except PluginNotAllowedError as exc:
            logger.debug("Skipped non-allowlisted plugin %s: %s", plugin_path, exc)
            continue

        if register_callback is not None:
            register_callback(module)
        loaded.append(module)

    return loaded
