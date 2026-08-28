"""Example plugin — disabled by default.

This file is not loaded until you add an allowlist entry with a matching
name and SHA-256 hash. Compute the hash with:

    python -c "import hashlib, pathlib; p=pathlib.Path('src/plugins/example_plugin.py'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
"""


def register_tools(mcp: object) -> None:
    """Register optional MCP tools from this plugin."""

    @mcp.tool()  # type: ignore[attr-defined]
    async def example_plugin_ping() -> str:
        """Example allowlisted plugin tool."""
        return "example_plugin_pong"
