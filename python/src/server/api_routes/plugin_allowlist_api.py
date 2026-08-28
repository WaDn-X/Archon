"""Plugin allowlist API endpoints."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.allowlist.models import AllowlistEntry, AllowlistFile
from src.allowlist.service import get_allowlist_service

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


class AllowlistUpdateRequest(BaseModel):
    """Replace or patch allowlist entries."""

    plugins: list[AllowlistEntry] | None = None
    executors: list[AllowlistEntry] | None = None


class AllowlistEntryActionRequest(BaseModel):
    """Add, remove, or toggle a single allowlist entry."""

    action: Literal["add", "remove", "enable", "disable"]
    section: Literal["plugins", "executors"]
    entry: AllowlistEntry | None = None
    name: str | None = Field(default=None, description="Entry name for remove/enable/disable")


@router.get("/allowlist")
async def get_plugin_allowlist() -> AllowlistFile:
    """Return the current plugin and executor allowlist."""
    return get_allowlist_service().load()


@router.put("/allowlist")
async def put_plugin_allowlist(body: AllowlistFile) -> AllowlistFile:
    """Replace the full plugin and executor allowlist."""
    service = get_allowlist_service()
    service.save(body)
    return service.load()


@router.post("/allowlist/entries")
async def mutate_allowlist_entry(body: AllowlistEntryActionRequest) -> AllowlistFile:
    """Add, remove, enable, or disable a single allowlist entry."""
    service = get_allowlist_service()
    allowlist = service.load()
    entries = allowlist.plugins if body.section == "plugins" else allowlist.executors

    if body.action == "add":
        if body.entry is None:
            raise HTTPException(status_code=400, detail={"error": "entry is required for add"})
        if any(item.name == body.entry.name for item in entries):
            raise HTTPException(status_code=409, detail={"error": f"Entry '{body.entry.name}' already exists"})
        entries.append(body.entry)
    else:
        if not body.name:
            raise HTTPException(status_code=400, detail={"error": "name is required for remove/enable/disable"})
        index = next((i for i, item in enumerate(entries) if item.name == body.name), None)
        if index is None:
            raise HTTPException(status_code=404, detail={"error": f"Entry '{body.name}' not found"})

        if body.action == "remove":
            entries.pop(index)
        elif body.action == "enable":
            entries[index] = entries[index].model_copy(update={"enabled": True})
        elif body.action == "disable":
            entries[index] = entries[index].model_copy(update={"enabled": False})

    if body.section == "plugins":
        allowlist.plugins = entries
    else:
        allowlist.executors = entries

    service.save(allowlist)
    return service.load()
