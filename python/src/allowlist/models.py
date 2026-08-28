"""Allowlist data models."""

from pydantic import BaseModel, Field


class AllowlistEntry(BaseModel):
    """Single allowlist entry for a plugin module or executor binary."""

    name: str = Field(..., min_length=1, description="Plugin module name or executor binary name")
    sha256: str = Field(..., min_length=64, max_length=64, description="SHA-256 hex digest of source bytes")
    enabled: bool = Field(default=True, description="Whether this entry is active")


class AllowlistFile(BaseModel):
    """On-disk allowlist configuration."""

    plugins: list[AllowlistEntry] = Field(default_factory=list)
    executors: list[AllowlistEntry] = Field(default_factory=list)
