"""
Document and version management tools for Archon MCP Server.

This module provides consolidated MCP tools for document operations:
- find_documents, manage_document
- find_versions, manage_version
"""

from .document_tools import register_document_tools
from .version_tools import register_version_tools

__all__ = ["register_document_tools", "register_version_tools"]
