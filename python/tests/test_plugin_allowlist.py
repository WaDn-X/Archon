"""Tests for the execute allowlist (plugins and sandbox executors)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.allowlist.exceptions import ExecutorNotAllowedError, PluginNotAllowedError
from src.allowlist.executors import FIRST_PARTY_EXECUTORS, validate_sandbox_command
from src.allowlist.loader import load_allowed_plugin, load_allowlisted_plugins_from_directory
from src.allowlist.models import AllowlistEntry, AllowlistFile
from src.allowlist.service import AllowlistService, compute_file_sha256


@pytest.fixture
def allowlist_path(tmp_path: Path) -> Path:
    return tmp_path / "plugin_allowlist.json"


@pytest.fixture
def allowlist_service(allowlist_path: Path) -> AllowlistService:
    return AllowlistService(allowlist_path)


@pytest.fixture(autouse=True)
def patch_allowlist_service(allowlist_service: AllowlistService, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.allowlist.service.get_allowlist_service", lambda: allowlist_service)
    monkeypatch.setattr("src.allowlist.loader.get_allowlist_service", lambda: allowlist_service)
    monkeypatch.setattr("src.allowlist.executors.get_allowlist_service", lambda: allowlist_service)


def _write_allowlist(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_empty_allowlist_loads_zero_plugins(tmp_path: Path, allowlist_service: AllowlistService) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "extra.py").write_text("VALUE = 1\n", encoding="utf-8")
    _write_allowlist(allowlist_service.path, {"plugins": [], "executors": []})

    loaded = load_allowlisted_plugins_from_directory(plugin_dir)
    assert loaded == []


def test_hash_match_loads_plugin(tmp_path: Path, allowlist_service: AllowlistService) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "demo_plugin.py"
    plugin_file.write_text("PLUGIN_VALUE = 'ok'\n", encoding="utf-8")
    plugin_hash = compute_file_sha256(plugin_file)
    _write_allowlist(
        allowlist_service.path,
        {"plugins": [{"name": "demo_plugin", "sha256": plugin_hash, "enabled": True}], "executors": []},
    )

    module = load_allowed_plugin(plugin_file)
    assert module.PLUGIN_VALUE == "ok"


def test_hash_mismatch_refuses_plugin(tmp_path: Path, allowlist_service: AllowlistService) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "demo_plugin.py"
    plugin_file.write_text("PLUGIN_VALUE = 'v1'\n", encoding="utf-8")
    _write_allowlist(
        allowlist_service.path,
        {"plugins": [{"name": "demo_plugin", "sha256": "0" * 64, "enabled": True}], "executors": []},
    )

    with pytest.raises(PluginNotAllowedError, match="hash mismatch"):
        load_allowed_plugin(plugin_file)


def test_unknown_name_refuses_plugin(tmp_path: Path, allowlist_service: AllowlistService) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "unknown.py"
    plugin_file.write_text("x = 1\n", encoding="utf-8")
    _write_allowlist(allowlist_service.path, {"plugins": [], "executors": []})

    with pytest.raises(PluginNotAllowedError, match="not allowlisted"):
        load_allowed_plugin(plugin_file)


def test_disabled_entry_refuses_plugin(tmp_path: Path, allowlist_service: AllowlistService) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "demo_plugin.py"
    plugin_file.write_text("x = 1\n", encoding="utf-8")
    plugin_hash = compute_file_sha256(plugin_file)
    _write_allowlist(
        allowlist_service.path,
        {"plugins": [{"name": "demo_plugin", "sha256": plugin_hash, "enabled": False}], "executors": []},
    )

    with pytest.raises(PluginNotAllowedError, match="disabled"):
        load_allowed_plugin(plugin_file)


def test_first_party_executors_always_allowed() -> None:
    for executor in FIRST_PARTY_EXECUTORS:
        validate_sandbox_command(f"{executor} --version")


def test_non_first_party_executor_requires_allowlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "custom-tool"
    fake_bin.write_bytes(b"#!/bin/sh\necho hi\n")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    with pytest.raises(ExecutorNotAllowedError, match="not allowlisted"):
        validate_sandbox_command("custom-tool run")


def test_allowlisted_executor_passes(tmp_path: Path, allowlist_service: AllowlistService, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "custom-tool"
    fake_bin.write_bytes(b"#!/bin/sh\necho hi\n")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    executor_hash = hashlib.sha256(fake_bin.read_bytes()).hexdigest()
    _write_allowlist(
        allowlist_service.path,
        {"plugins": [], "executors": [{"name": "custom-tool", "sha256": executor_hash, "enabled": True}]},
    )

    validate_sandbox_command("custom-tool run")


def test_builtin_mcp_tools_register_without_allowlist_entries() -> None:
    """Built-in MCP modules register via static imports, not the plugin loader."""
    from src.mcp_server.features.rag import register_rag_tools

    registered: list[str] = []
    mock_mcp = MagicMock()

    def tool_decorator(*_args, **_kwargs):
        def wrapper(fn):
            registered.append(fn.__name__)
            return fn

        return wrapper

    mock_mcp.tool = tool_decorator
    register_rag_tools(mock_mcp)
    assert "rag_search_knowledge_base" in registered


def test_plugin_path_outside_directory_is_rejected(
	tmp_path: Path, allowlist_service: AllowlistService
) -> None:
	plugin_dir = tmp_path / "plugins"
	plugin_dir.mkdir()
	plugin_file = plugin_dir / "demo_plugin.py"
	plugin_file.write_text("PLUGIN_VALUE = 'ok'\n", encoding="utf-8")
	outside_file = tmp_path / "outside.py"
	outside_file.write_text("PLUGIN_VALUE = 'bad'\n", encoding="utf-8")
	plugin_hash = compute_file_sha256(outside_file)
	_write_allowlist(
		allowlist_service.path,
		{"plugins": [{"name": "outside", "sha256": plugin_hash, "enabled": True}], "executors": []},
	)

	with pytest.raises(PluginNotAllowedError, match="outside the allowed plugin directory"):
		load_allowed_plugin(outside_file, allowed_root=plugin_dir)


def test_allowlist_api_roundtrip(allowlist_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    api_path = Path(__file__).resolve().parents[1] / "src" / "server" / "api_routes" / "plugin_allowlist_api.py"
    spec = importlib.util.spec_from_file_location("plugin_allowlist_api_test", api_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    service = AllowlistService(allowlist_path)
    monkeypatch.setattr(module, "get_allowlist_service", lambda: service)
    monkeypatch.setattr(module, "is_internal_request", lambda _request: True)

    app = FastAPI()
    app.include_router(module.router)
    client = TestClient(app)

    payload = AllowlistFile(
        plugins=[AllowlistEntry(name="demo", sha256="a" * 64, enabled=True)],
        executors=[],
    )
    put_response = client.put("/api/plugins/allowlist", json=payload.model_dump())
    assert put_response.status_code == 200

    get_response = client.get("/api/plugins/allowlist")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["plugins"][0]["name"] == "demo"


def test_allowlist_api_entry_mutations(allowlist_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    api_path = Path(__file__).resolve().parents[1] / "src" / "server" / "api_routes" / "plugin_allowlist_api.py"
    spec = importlib.util.spec_from_file_location("plugin_allowlist_api_entries_test", api_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    service = AllowlistService(allowlist_path)
    monkeypatch.setattr(module, "get_allowlist_service", lambda: service)
    monkeypatch.setattr(module, "is_internal_request", lambda _request: True)

    app = FastAPI()
    app.include_router(module.router)
    client = TestClient(app)

    add_response = client.post(
        "/api/plugins/allowlist/entries",
        json={
            "action": "add",
            "section": "plugins",
            "entry": {"name": "demo", "sha256": "b" * 64, "enabled": False},
        },
    )
    assert add_response.status_code == 200
    assert add_response.json()["plugins"][0]["enabled"] is False

    enable_response = client.post(
        "/api/plugins/allowlist/entries",
        json={"action": "enable", "section": "plugins", "name": "demo"},
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["plugins"][0]["enabled"] is True

    remove_response = client.post(
        "/api/plugins/allowlist/entries",
        json={"action": "remove", "section": "plugins", "name": "demo"},
    )
    assert remove_response.status_code == 200
    assert remove_response.json()["plugins"] == []


def test_discovered_plugins_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    api_path = Path(__file__).resolve().parents[1] / "src" / "server" / "api_routes" / "plugin_allowlist_api.py"
    spec = importlib.util.spec_from_file_location("plugin_allowlist_api_discovered_test", api_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    app = FastAPI()
    app.include_router(module.router)
    client = TestClient(app)

    response = client.get("/api/plugins/discovered")
    assert response.status_code == 200
    names = response.json()
    assert isinstance(names, list)
    assert "example_plugin" in names


def test_allowlist_api_blocks_external_writes(allowlist_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    api_path = Path(__file__).resolve().parents[1] / "src" / "server" / "api_routes" / "plugin_allowlist_api.py"
    spec = importlib.util.spec_from_file_location("plugin_allowlist_api_test_external", api_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    service = AllowlistService(allowlist_path)
    monkeypatch.setattr(module, "get_allowlist_service", lambda: service)
    monkeypatch.setattr(module, "is_internal_request", lambda _request: False)

    app = FastAPI()
    app.include_router(module.router)
    client = TestClient(app)

    payload = AllowlistFile(plugins=[], executors=[])
    put_response = client.put("/api/plugins/allowlist", json=payload.model_dump())
    assert put_response.status_code == 403
