"""Ensure MCP client instructions reference registered tool names."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_PATH = REPO_ROOT / "src" / "mcp_server" / "mcp_server.py"
FEATURES_ROOT = REPO_ROOT / "src" / "mcp_server" / "features"

STALE_TOOL_NAMES = ("list_tasks", "list_projects", "list_documents", "list_versions")
EXPECTED_FIND_TOOLS = ("find_tasks", "find_projects", "find_documents", "find_versions")
EXPECTED_MANAGE_TOOLS = ("manage_task", "manage_project", "manage_document", "manage_version")


def _extract_mcp_instructions() -> str:
	text = MCP_SERVER_PATH.read_text(encoding="utf-8")
	match = re.search(r'MCP_INSTRUCTIONS = """(.*?)"""', text, re.DOTALL)
	assert match is not None, "MCP_INSTRUCTIONS block not found in mcp_server.py"
	return match.group(1)


def _collect_registered_tool_names() -> set[str]:
	names: set[str] = set()
	pattern = re.compile(r"@mcp\.tool\(\)\s+async def (\w+)")
	for path in FEATURES_ROOT.rglob("*.py"):
		for match in pattern.finditer(path.read_text(encoding="utf-8")):
			names.add(match.group(1))
	# Built-in tools declared in mcp_server.py
	server_source = MCP_SERVER_PATH.read_text(encoding="utf-8")
	for match in pattern.finditer(server_source):
		names.add(match.group(1))
	return names


def test_mcp_instructions_do_not_reference_stale_list_tools() -> None:
	instructions = _extract_mcp_instructions()
	for stale in STALE_TOOL_NAMES:
		assert stale not in instructions, f"MCP_INSTRUCTIONS still mentions stale tool {stale!r}"


def test_mcp_instructions_reference_find_and_manage_tools() -> None:
	instructions = _extract_mcp_instructions()
	for tool_name in (*EXPECTED_FIND_TOOLS, *EXPECTED_MANAGE_TOOLS):
		assert tool_name in instructions, f"MCP_INSTRUCTIONS missing documented tool {tool_name!r}"


def test_documented_core_tools_are_registered() -> None:
	registered = _collect_registered_tool_names()
	for tool_name in (*EXPECTED_FIND_TOOLS, *EXPECTED_MANAGE_TOOLS):
		assert tool_name in registered, f"Documented tool {tool_name!r} is not registered via @mcp.tool"


@pytest.mark.parametrize(
	"relative_path,stale_names",
	[
		("features/tasks/__init__.py", ("list_tasks",)),
		("features/projects/__init__.py", ("list_projects",)),
		("features/documents/__init__.py", ("list_documents", "list_versions")),
	],
)
def test_feature_module_docstrings_avoid_stale_names(relative_path: str, stale_names: tuple[str, ...]) -> None:
	text = (REPO_ROOT / "src" / "mcp_server" / relative_path).read_text(encoding="utf-8")
	for stale in stale_names:
		assert stale not in text, f"{relative_path} still documents stale tool {stale!r}"
