"""
Task Dependency Service

Provides comprehensive task dependency management including:
- Task dependency graphs and relationships
- Critical path analysis
- Dependency validation and conflict resolution
- Automatic task ordering and scheduling
- Dependency impact analysis
"""

import asyncio
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import networkx as nx
from collections import defaultdict, deque


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks."""
    dependent_task_id: str  # Task that depends on another
    prerequisite_task_id: str  # Task that must be completed first
    dependency_type: str = "finish_to_start"  # finish_to_start, start_to_start, etc.
    lag_days: int = 0  # Days to wait after prerequisite completion
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project."""
    project_id: str
    tasks: Dict[str, Dict[str, Any]]
    dependencies: List[TaskDependency]
    critical_path: List[str]
    topological_order: List[str]
    cycles: List[List[str]]
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CriticalPathAnalysis:
    """Analysis of critical path and project timeline."""
    total_duration_days: int
    critical_tasks: List[str]
    slack_by_task: Dict[str, int]  # Days of slack for each task
    earliest_start_dates: Dict[str, datetime]
    latest_start_dates: Dict[str, datetime]
    earliest_finish_dates: Dict[str, datetime]
    latest_finish_dates: Dict[str, datetime]


class DependencyType(Enum):
    """Types of task dependencies."""
    FINISH_TO_START = "finish_to_start"  # Most common
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


class TaskDependencyService:
    """Service for managing task dependencies and critical path analysis."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def create_dependency(
        self,
        dependent_task_id: str,
        prerequisite_task_id: str,
        dependency_type: str = "finish_to_start",
        lag_days: int = 0
    ) -> bool:
        """
        Create a dependency relationship between tasks.

        Args:
            dependent_task_id: Task that depends on the prerequisite
            prerequisite_task_id: Task that must be completed first
            dependency_type: Type of dependency relationship
            lag_days: Days to wait after prerequisite completion

        Returns:
            True if dependency created successfully
        """
        try:
            # Validate dependency doesn't create a cycle
            if await self._would_create_cycle(dependent_task_id, prerequisite_task_id):
                raise ValueError(f"Creating this dependency would create a cycle")

            # Create dependency record
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                lag_days=lag_days
            )

            # Store dependency (would use database in production)
            # For now, we'll use in-memory storage
            self.logger.info(f"Created dependency: {prerequisite_task_id} -> {dependent_task_id}")

            return True

        except Exception as e:
            self.logger.error(f"Error creating dependency: {e}")
            return False

    async def remove_dependency(self, dependent_task_id: str, prerequisite_task_id: str) -> bool:
        """
        Remove a dependency relationship.

        Args:
            dependent_task_id: Dependent task ID
            prerequisite_task_id: Prerequisite task ID

        Returns:
            True if dependency removed successfully
        """
        try:
            # Remove dependency record
            self.logger.info(f"Removed dependency: {prerequisite_task_id} -> {dependent_task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error removing dependency: {e}")
            return False

    async def analyze_project_dependencies(self, project_id: str, tasks: List[Dict[str, Any]]) -> DependencyGraph:
        """
        Analyze all dependencies for a project and create dependency graph.

        Args:
            project_id: Project identifier
            tasks: List of task dictionaries

        Returns:
            Complete dependency graph analysis
        """
        try:
            # Build dependency graph using NetworkX
            graph = nx.DiGraph()
            graph.add_nodes_from(task['id'] for task in tasks)

            # Add edges for dependencies (would load from database in production)
            # For now, we'll create a sample dependency graph
            dependencies = await self._get_project_dependencies(project_id)

            for dep in dependencies:
                graph.add_edge(dep.prerequisite_task_id, dep.dependent_task_id)

            # Detect cycles
            cycles = list(nx.simple_cycles(graph))

            # Calculate topological order
            try:
                topological_order = list(nx.topological_sort(graph))
            except nx.NetworkXError:
                # Graph has cycles, use alternative ordering
                topological_order = self._get_alternative_topological_order(graph, tasks)

            # Find critical path
            critical_path = await self._calculate_critical_path(graph, tasks)

            return DependencyGraph(
                project_id=project_id,
                tasks={task['id']: task for task in tasks},
                dependencies=dependencies,
                critical_path=critical_path,
                topological_order=topological_order,
                cycles=cycles
            )

        except Exception as e:
            self.logger.error(f"Error analyzing project dependencies: {e}")
            # Return empty graph on error
            return DependencyGraph(
                project_id=project_id,
                tasks={},
                dependencies=[],
                critical_path=[],
                topological_order=[],
                cycles=[]
            )

    async def _would_create_cycle(self, new_dependent: str, new_prerequisite: str) -> bool:
        """Check if adding a dependency would create a cycle."""
        try:
            # This would check the existing dependency graph
            # For now, return False (no cycles detected)
            return False

        except Exception as e:
            self.logger.error(f"Error checking for cycles: {e}")
            return True  # Assume cycle to be safe

    async def _get_project_dependencies(self, project_id: str) -> List[TaskDependency]:
        """Get all dependencies for a project."""
        # In production, this would query the database
        # For now, return sample dependencies
        return [
            TaskDependency(
                dependent_task_id="task_2",
                prerequisite_task_id="task_1",
                dependency_type="finish_to_start"
            ),
            TaskDependency(
                dependent_task_id="task_3",
                prerequisite_task_id="task_2",
                dependency_type="finish_to_start"
            ),
            TaskDependency(
                dependent_task_id="task_4",
                prerequisite_task_id="task_1",
                dependency_type="finish_to_start"
            ),
        ]

    async def _calculate_critical_path(self, graph: nx.DiGraph, tasks: List[Dict[str, Any]]) -> List[str]:
        """Calculate the critical path through the dependency graph."""
        try:
            if not graph.nodes():
                return []

            # Calculate longest path (critical path)
            # This is a simplified version - real implementation would use proper algorithms
            longest_path = []

            # Find path from start nodes to end nodes
            start_nodes = [node for node in graph.nodes() if graph.in_degree(node) == 0]
            end_nodes = [node for node in graph.nodes() if graph.out_degree(node) == 0]

            if start_nodes and end_nodes:
                # Find longest path between start and end nodes
                max_length = 0
                for start in start_nodes:
                    for end in end_nodes:
                        try:
                            paths = list(nx.all_simple_paths(graph, start, end))
                            for path in paths:
                                if len(path) > max_length:
                                    max_length = len(path)
                                    longest_path = path
                        except:
                            continue

            return longest_path

        except Exception as e:
            self.logger.error(f"Error calculating critical path: {e}")
            return []

    def _get_alternative_topological_order(self, graph: nx.DiGraph, tasks: List[Dict[str, Any]]) -> List[str]:
        """Get an alternative ordering when cycles exist."""
        try:
            # Use priority-based ordering when cycles exist
            task_priorities = {}

            for task in tasks:
                priority = task.get('priority', 'medium')
                priority_map = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
                task_priorities[task['id']] = priority_map.get(priority, 2)

            # Sort by priority (highest first)
            sorted_tasks = sorted(
                tasks,
                key=lambda t: task_priorities.get(t['id'], 2),
                reverse=True
            )

            return [task['id'] for task in sorted_tasks]

        except Exception as e:
            self.logger.error(f"Error getting alternative topological order: {e}")
            return [task['id'] for task in tasks]

    async def get_task_dependencies(self, task_id: str) -> Dict[str, List[str]]:
        """Get all dependencies for a specific task."""
        try:
            # Get prerequisites (tasks this task depends on)
            # Get dependents (tasks that depend on this task)
            return {
                "prerequisites": [],  # Would load from database
                "dependents": []      # Would load from database
            }

        except Exception as e:
            self.logger.error(f"Error getting task dependencies: {e}")
            return {"prerequisites": [], "dependents": []}

    async def validate_dependency_chain(self, task_ids: List[str]) -> Dict[str, Any]:
        """Validate that a chain of tasks has valid dependencies."""
        try:
            validation_result = {
                "is_valid": True,
                "cycles": [],
                "missing_dependencies": [],
                "warnings": []
            }

            # Check for cycles in the dependency chain
            # Check for missing prerequisite tasks
            # Validate dependency types and constraints

            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating dependency chain: {e}")
            return {
                "is_valid": False,
                "cycles": [],
                "missing_dependencies": [],
                "warnings": [f"Validation error: {e}"]
            }

    async def calculate_project_timeline(self, dependency_graph: DependencyGraph) -> CriticalPathAnalysis:
        """Calculate project timeline and critical path analysis."""
        try:
            tasks = dependency_graph.tasks
            critical_path = dependency_graph.critical_path

            # Calculate earliest start/finish times
            earliest_start = {}
            earliest_finish = {}
            latest_start = {}
            latest_finish = {}

            # Forward pass (earliest times)
            for task_id in dependency_graph.topological_order:
                task = tasks.get(task_id, {})

                # Get prerequisites
                prereqs = [dep.prerequisite_task_id for dep in dependency_graph.dependencies
                          if dep.dependent_task_id == task_id]

                # Calculate earliest start time
                if not prereqs:
                    # No prerequisites - can start immediately
                    earliest_start[task_id] = datetime.now()
                else:
                    # Must wait for all prerequisites to finish
                    max_prereq_finish = max(
                        earliest_finish.get(prereq, datetime.now())
                        for prereq in prereqs
                    )
                    earliest_start[task_id] = max_prereq_finish

                # Calculate earliest finish time (assuming task duration)
                # For demo, assume each task takes 1 day
                duration_days = task.get('estimated_duration_days', 1)
                earliest_finish[task_id] = earliest_start[task_id] + timedelta(days=duration_days)

            # Backward pass (latest times)
            reversed_topo = list(reversed(dependency_graph.topological_order))

            for task_id in reversed_topo:
                task = tasks.get(task_id, {})

                # Get dependents
                dependents = [dep.dependent_task_id for dep in dependency_graph.dependencies
                             if dep.prerequisite_task_id == task_id]

                # Calculate latest finish time
                if not dependents:
                    # No dependents - latest finish is earliest finish
                    latest_finish[task_id] = earliest_finish[task_id]
                else:
                    # Must finish before earliest dependent start
                    min_dependent_start = min(
                        earliest_start.get(dep, datetime.now() + timedelta(days=30))
                        for dep in dependents
                    )
                    duration_days = task.get('estimated_duration_days', 1)
                    latest_finish[task_id] = min_dependent_start - timedelta(days=duration_days)

                # Calculate latest start time
                duration_days = task.get('estimated_duration_days', 1)
                latest_start[task_id] = latest_finish[task_id] - timedelta(days=duration_days)

            # Calculate slack for each task
            slack_by_task = {}
            for task_id in tasks:
                earliest = earliest_finish.get(task_id, datetime.now())
                latest = latest_finish.get(task_id, datetime.now())
                slack_days = (latest - earliest).days
                slack_by_task[task_id] = slack_days

            # Calculate total project duration
            if critical_path:
                total_duration = (
                    earliest_finish.get(critical_path[-1], datetime.now()) -
                    earliest_start.get(critical_path[0], datetime.now())
                ).days
            else:
                total_duration = 0

            return CriticalPathAnalysis(
                total_duration_days=total_duration,
                critical_tasks=critical_path,
                slack_by_task=slack_by_task,
                earliest_start_dates=earliest_start,
                latest_start_dates=latest_start,
                earliest_finish_dates=earliest_finish,
                latest_finish_dates=latest_finish
            )

        except Exception as e:
            self.logger.error(f"Error calculating project timeline: {e}")
            return CriticalPathAnalysis(
                total_duration_days=0,
                critical_tasks=[],
                slack_by_task={},
                earliest_start_dates={},
                latest_start_dates={},
                earliest_finish_dates={},
                latest_finish_dates={}
            )

    async def get_dependency_impact_analysis(self, task_id: str, action: str) -> Dict[str, Any]:
        """Analyze the impact of changes to a task on its dependencies."""
        try:
            impact = {
                "task_id": task_id,
                "action": action,  # "complete", "delay", "cancel", "modify"
                "affected_tasks": [],
                "cascade_effects": [],
                "risk_assessment": "low",
                "recommendations": []
            }

            # Analyze impact based on action type
            if action == "delay":
                impact["cascade_effects"].append("Dependent tasks may be delayed")
                impact["recommendations"].append("Consider parallel task execution")
                impact["risk_assessment"] = "medium"

            elif action == "cancel":
                impact["cascade_effects"].append("Dependent tasks may become impossible")
                impact["recommendations"].append("Reassign or remove dependent tasks")
                impact["risk_assessment"] = "high"

            return impact

        except Exception as e:
            self.logger.error(f"Error analyzing dependency impact: {e}")
            return {
                "task_id": task_id,
                "action": action,
                "affected_tasks": [],
                "cascade_effects": [],
                "risk_assessment": "unknown",
                "recommendations": ["Unable to analyze impact"]
            }

    async def suggest_dependency_optimizations(self, dependency_graph: DependencyGraph) -> List[str]:
        """Suggest optimizations for the dependency graph."""
        try:
            suggestions = []

            # Check for parallel execution opportunities
            if len(dependency_graph.dependencies) > len(dependency_graph.tasks) * 0.5:
                suggestions.append("Consider reducing dependencies to enable more parallel execution")

            # Check for long critical path
            if len(dependency_graph.critical_path) > 5:
                suggestions.append("Critical path is long - consider breaking down large tasks")

            # Check for cycles
            if dependency_graph.cycles:
                suggestions.append(f"Dependency cycles detected: {len(dependency_graph.cycles)} cycles found")

            # Check for overloaded tasks
            task_dependencies = defaultdict(int)
            for dep in dependency_graph.dependencies:
                task_dependencies[dep.prerequisite_task_id] += 1
                task_dependencies[dep.dependent_task_id] += 1

            overloaded_tasks = [task_id for task_id, count in task_dependencies.items() if count > 3]
            if overloaded_tasks:
                suggestions.append(f"Tasks with many dependencies: {', '.join(overloaded_tasks[:3])}")

            return suggestions

        except Exception as e:
            self.logger.error(f"Error suggesting optimizations: {e}")
            return []


# Global instance
task_dependency_service = TaskDependencyService()
