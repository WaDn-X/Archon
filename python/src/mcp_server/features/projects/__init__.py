"""
Project management tools for Archon MCP Server.

This module provides consolidated MCP tools for project operations:
- find_projects: List, search, and get projects
- manage_project: Create, update, and delete projects
"""

from .project_tools import register_project_tools

__all__ = ["register_project_tools"]
