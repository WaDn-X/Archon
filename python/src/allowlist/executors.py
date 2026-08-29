"""Sandbox executor validation for agent work orders."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

from .exceptions import ExecutorNotAllowedError
from .service import get_allowlist_service

# First-party executors are always permitted without allowlist entries.
FIRST_PARTY_EXECUTORS: frozenset[str] = frozenset({"claude", "git", "gh"})


def _resolve_configured_binary(name: str) -> str | None:
    """Map first-party executor names to configured CLI paths when set."""
    if name == "claude":
        return os.getenv("CLAUDE_CLI_PATH", "claude")
    if name == "gh":
        return os.getenv("GH_CLI_PATH", "gh")
    return name


def _extract_executable_name(command: str) -> str:
    parts = shlex.split(command, posix=True)
    if not parts:
        raise ExecutorNotAllowedError("Empty command is not allowed")
    executable = Path(parts[0]).name
    return executable


def validate_sandbox_command(command: str) -> None:
    """Validate that a sandbox shell command uses an allowed executor.

    First-party executors (claude, git, gh) are always allowed.
    Any other binary must have a matching enabled allowlist entry with
    the same name and SHA-256 hash of the resolved binary on disk.
    """
    executable_name = _extract_executable_name(command)

    if executable_name in FIRST_PARTY_EXECUTORS:
        return

    configured = _resolve_configured_binary(executable_name)
    binary_path = shutil.which(configured or executable_name)
    if binary_path is None:
        raise ExecutorNotAllowedError(
            f"Executor '{executable_name}' is not a first-party binary and was not found on PATH"
        )

    get_allowlist_service().verify_executor_binary(executable_name, Path(binary_path))
