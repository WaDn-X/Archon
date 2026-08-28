"""Allowlist configuration load/save and validation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .exceptions import AllowlistError, ExecutorNotAllowedError, PluginNotAllowedError
from .models import AllowlistEntry, AllowlistFile

DEFAULT_ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / "server" / "config" / "plugin_allowlist.json"


def _default_allowlist_path() -> Path:
    env_path = os.getenv("PLUGIN_ALLOWLIST_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_ALLOWLIST_PATH


def compute_file_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class AllowlistService:
    """Loads and validates plugin and executor allowlist entries."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _default_allowlist_path()

    def load(self) -> AllowlistFile:
        if not self.path.exists():
            return AllowlistFile()

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AllowlistError(f"Invalid allowlist JSON at {self.path}: {exc}") from exc

        return AllowlistFile.model_validate(raw)

    def save(self, allowlist: AllowlistFile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = allowlist.model_dump()
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def get_plugin_entry(self, name: str) -> AllowlistEntry | None:
        for entry in self.load().plugins:
            if entry.name == name:
                return entry
        return None

    def get_executor_entry(self, name: str) -> AllowlistEntry | None:
        for entry in self.load().executors:
            if entry.name == name:
                return entry
        return None

    def verify_plugin(self, plugin_path: Path, expected_name: str | None = None) -> AllowlistEntry:
        """Verify a plugin file against the allowlist.

        Args:
            plugin_path: Path to the plugin source file.
            expected_name: Optional explicit name; defaults to file stem.

        Returns:
            The matching allowlist entry.

        Raises:
            PluginNotAllowedError: If the plugin is missing, disabled, or mismatched.
        """
        if not plugin_path.is_file():
            raise PluginNotAllowedError(f"Plugin file not found: {plugin_path}")

        name = expected_name or plugin_path.stem
        entry = self.get_plugin_entry(name)
        if entry is None:
            raise PluginNotAllowedError(
                f"Plugin '{name}' is not allowlisted. "
                f"Add an entry with matching name and SHA-256 to {self.path}"
            )

        if not entry.enabled:
            raise PluginNotAllowedError(f"Plugin '{name}' is allowlisted but disabled")

        actual_hash = compute_file_sha256(plugin_path)
        if actual_hash != entry.sha256.lower():
            raise PluginNotAllowedError(
                f"Plugin '{name}' hash mismatch. "
                f"Expected {entry.sha256}, got {actual_hash}. "
                "Update the allowlist entry after reviewing the plugin source."
            )

        return entry

    def verify_executor_binary(self, binary_name: str, binary_path: Path) -> AllowlistEntry:
        """Verify an executor binary against the allowlist."""
        entry = self.get_executor_entry(binary_name)
        if entry is None:
            raise ExecutorNotAllowedError(
                f"Executor '{binary_name}' is not allowlisted. "
                f"Add an entry with matching name and SHA-256 to {self.path}"
            )

        if not entry.enabled:
            raise ExecutorNotAllowedError(f"Executor '{binary_name}' is allowlisted but disabled")

        if not binary_path.is_file():
            raise ExecutorNotAllowedError(f"Executor binary not found: {binary_path}")

        actual_hash = compute_file_sha256(binary_path)
        if actual_hash != entry.sha256.lower():
            raise ExecutorNotAllowedError(
                f"Executor '{binary_name}' hash mismatch. "
                f"Expected {entry.sha256}, got {actual_hash}."
            )

        return entry


_allowlist_service: AllowlistService | None = None


def get_allowlist_service(path: Path | None = None) -> AllowlistService:
    """Return a shared allowlist service instance."""
    global _allowlist_service
    if path is not None:
        return AllowlistService(path)
    if _allowlist_service is None:
        _allowlist_service = AllowlistService()
    return _allowlist_service
