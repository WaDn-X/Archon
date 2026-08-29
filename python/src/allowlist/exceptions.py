"""Allowlist-related exceptions."""


class AllowlistError(Exception):
    """Base exception for allowlist failures."""


class PluginNotAllowedError(AllowlistError):
    """Raised when a plugin cannot be loaded because it is not allowlisted."""


class ExecutorNotAllowedError(AllowlistError):
    """Raised when a sandbox command uses a non-allowlisted executor."""
