"""Optional Archon plugin modules.

Only plugins with matching name and SHA-256 entries in the execute allowlist
are loaded at runtime. An empty allowlist means zero extra plugins run.
"""

from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent

__all__ = ["PLUGIN_DIR"]
