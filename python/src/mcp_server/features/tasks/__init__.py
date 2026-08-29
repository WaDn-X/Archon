"""
Task management tools for Archon MCP Server.

This module provides consolidated MCP tools for task operations:
- find_tasks: List, search, and get tasks with filtering
- manage_task: Create, update, and delete tasks
"""

from .task_tools import register_task_tools

__all__ = ["register_task_tools"]
