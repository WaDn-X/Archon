"""Plugin allowlist API endpoints."""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.allowlist.models import AllowlistEntry, AllowlistFile
from src.allowlist.service import get_allowlist_service
from src.server.security.request_origin import is_internal_request

logger = logging.getLogger(__name__)

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
async def put_plugin_allowlist(body: AllowlistFile, request: Request) -> AllowlistFile:
    """Replace the full plugin and executor allowlist."""
    if not is_internal_request(request):
        client_host = request.client.host if request.client else "unknown"
        logger.warning("Blocked allowlist write from non-internal host %s", client_host)
        raise HTTPException(status_code=403, detail={"error": "Allowlist writes are restricted to local/internal requests"})
    service = get_allowlist_service()
    service.save(body)
    return service.load()


@router.post("/allowlist/entries")
async def mutate_allowlist_entry(body: AllowlistEntryActionRequest, request: Request) -> AllowlistFile:
    """Add, remove, enable, or disable a single allowlist entry."""
    if not is_internal_request(request):
        client_host = request.client.host if request.client else "unknown"
        logger.warning("Blocked allowlist mutation from non-internal host %s", client_host)
        raise HTTPException(status_code=403, detail={"error": "Allowlist writes are restricted to local/internal requests"})
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
