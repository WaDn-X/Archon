"""
Task Dependency Mapping and Visualization Service

Provides comprehensive task dependency analysis including:
- Automatic dependency detection and mapping
- Critical path analysis
- Dependency visualization
- Impact analysis for task changes
- Cycle detection and resolution
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from ..utils import get_enhanced_supabase_client
from .error_service import error_service


class DependencyType(Enum):
    """Types of task dependencies."""
    FINISH_TO_START = "finish_to_start"  # Task B can't start until Task A finishes
    START_TO_START = "start_to_start"    # Task B can't start until Task A starts
    FINISH_TO_FINISH = "finish_to_finish"  # Task B can't finish until Task A finishes
    START_TO_FINISH = "start_to_finish"  # Task B can't finish until Task A starts


class DependencyStrength(Enum):
    """Strength of dependency relationships."""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    CRITICAL = "critical"


@dataclass
class TaskNode:
    """Node in the task dependency graph."""
    task_id: str
    title: str
    status: str
    estimated_duration: Optional[int] = None  # in hours
    actual_duration: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDependency:
    """Represents a dependency between two tasks."""
    from_task: str
    to_task: str
    dependency_type: DependencyType
    strength: DependencyStrength
    lag_time: int = 0  # Lag time in hours
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticalPathResult:
    """Result of critical path analysis."""
    critical_path: List[str]
    total_duration: int
    slack_times: Dict[str, int]
    earliest_start: Dict[str, datetime]
    latest_start: Dict[str, datetime]
    earliest_finish: Dict[str, datetime]
    latest_finish: Dict[str, datetime]


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project."""
    project_id: str
    nodes: Dict[str, TaskNode]
    edges: List[TaskDependency]
    cycles: List[List[str]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class TaskDependencyService:
    """Service for managing and analyzing task dependencies."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = get_enhanced_supabase_client()
        self._graph_cache: Dict[str, DependencyGraph] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def build_dependency_graph(self, project_id: str) -> DependencyGraph:
        """
        Build a complete dependency graph for a project.

        Args:
            project_id: Project identifier

        Returns:
            Complete dependency graph
        """
        try:
            # Check cache first
            if self._is_cache_valid(project_id):
                return self._graph_cache[project_id]

            # Fetch project tasks
            tasks = await self._fetch_project_tasks(project_id)
            if not tasks:
                return DependencyGraph(project_id=project_id, nodes={}, edges=[])

            # Create task nodes
            nodes = {}
            for task in tasks:
                node = TaskNode(
                    task_id=task["id"],
                    title=task["title"],
                    status=task["status"],
                    estimated_duration=task.get("estimated_duration"),
                    actual_duration=task.get("actual_duration"),
                    start_date=self._parse_datetime(task.get("start_date")),
                    end_date=self._parse_datetime(task.get("end_date")),
                    metadata=task
                )
                nodes[task["id"]] = node

            # Build dependency edges
            edges = await self._build_dependency_edges(project_id, nodes)

            # Detect cycles
            cycles = self._detect_cycles(nodes, edges)

            # Create dependency graph
            graph = DependencyGraph(
                project_id=project_id,
                nodes=nodes,
                edges=edges,
                cycles=cycles,
                last_updated=datetime.now()
            )

            # Cache the graph
            self._graph_cache[project_id] = graph
            self._cache_expiry[project_id] = datetime.now() + timedelta(minutes=15)

            self.logger.info(f"Built dependency graph for project {project_id} with {len(nodes)} nodes and {len(edges)} edges")
            return graph

        except Exception as e:
            self.logger.error(f"Error building dependency graph for project {project_id}: {e}")
            error_service.log_error(
                "DEPENDENCY_GRAPH_BUILD_ERROR",
                f"Failed to build dependency graph for project {project_id}",
                {"project_id": project_id, "error": str(e)}
            )
            return DependencyGraph(project_id=project_id, nodes={}, edges=[])

    async def _fetch_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetch all tasks for a project."""
        try:
            response = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={"project_id": project_id}
            )
            return response.get("data", [])
        except Exception as e:
            self.logger.error(f"Error fetching project tasks: {e}")
            return []

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return None

    async def _build_dependency_edges(
        self,
        project_id: str,
        nodes: Dict[str, TaskNode]
    ) -> List[TaskDependency]:
        """Build dependency edges from explicit and implicit relationships."""
        edges = []

        # Fetch explicit dependencies from database
        explicit_dependencies = await self._fetch_explicit_dependencies(project_id)
        edges.extend(explicit_dependencies)

        # Detect implicit dependencies
        implicit_dependencies = self._detect_implicit_dependencies(nodes)
        edges.extend(implicit_dependencies)

        # Update node relationships
        for edge in edges:
            if edge.from_task in nodes and edge.to_task in nodes:
                nodes[edge.from_task].successors.add(edge.to_task)
                nodes[edge.to_task].predecessors.add(edge.from_task)

        return edges

    async def _fetch_explicit_dependencies(self, project_id: str) -> List[TaskDependency]:
        """Fetch explicit dependencies from database."""
        try:
            # This would query a dependencies table
            # For now, return empty list as explicit dependencies aren't stored yet
            return []
        except Exception as e:
            self.logger.warning(f"Error fetching explicit dependencies: {e}")
            return []

    def _detect_implicit_dependencies(self, nodes: Dict[str, TaskNode]) -> List[TaskDependency]:
        """Detect implicit dependencies based on task relationships."""
        dependencies = []

        task_list = list(nodes.values())

        for i, task_a in enumerate(task_list):
            for j, task_b in enumerate(task_list[i + 1:], i + 1):
                # Check for implicit dependencies based on various factors
                dependency = self._analyze_task_relationship(task_a, task_b)
                if dependency:
                    dependencies.append(dependency)

        return dependencies

    def _analyze_task_relationship(
        self,
        task_a: TaskNode,
        task_b: TaskNode
    ) -> Optional[TaskDependency]:
        """Analyze relationship between two tasks to detect implicit dependencies."""

        # Check for keyword-based dependencies
        if self._share_keywords(task_a, task_b):
            return TaskDependency(
                from_task=task_a.task_id,
                to_task=task_b.task_id,
                dependency_type=DependencyType.FINISH_TO_START,
                strength=DependencyStrength.WEAK,
                metadata={"reason": "shared_keywords"}
            )

        # Check for resource conflicts
        if self._have_resource_conflicts(task_a, task_b):
            return TaskDependency(
                from_task=task_a.task_id,
                to_task=task_b.task_id,
                dependency_type=DependencyType.START_TO_START,
                strength=DependencyStrength.MEDIUM,
                metadata={"reason": "resource_conflict"}
            )

        # Check for sequential naming patterns
        if self._are_sequential_tasks(task_a, task_b):
            return TaskDependency(
                from_task=task_a.task_id,
                to_task=task_b.task_id,
                dependency_type=DependencyType.FINISH_TO_START,
                strength=DependencyStrength.STRONG,
                metadata={"reason": "sequential_pattern"}
            )

        return None

    def _share_keywords(self, task_a: TaskNode, task_b: TaskNode) -> bool:
        """Check if two tasks share significant keywords."""
        title_a = set(task_a.title.lower().split())
        title_b = set(task_b.title.lower().split())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        title_a = title_a - stop_words
        title_b = title_b - stop_words

        # Check for significant overlap
        intersection = title_a & title_b
        return len(intersection) >= 2 and len(intersection) / len(title_a | title_b) > 0.3

    def _have_resource_conflicts(self, task_a: TaskNode, task_b: TaskNode) -> bool:
        """Check if two tasks have resource conflicts."""
        # This would check for shared resources that can't be used simultaneously
        # For now, check if they have the same assignee
        assignee_a = task_a.metadata.get("assignee")
        assignee_b = task_b.metadata.get("assignee")

        if assignee_a and assignee_b and assignee_a == assignee_b:
            # Check if their time ranges overlap
            return self._time_ranges_overlap(task_a, task_b)

        return False

    def _are_sequential_tasks(self, task_a: TaskNode, task_b: TaskNode) -> bool:
        """Check if tasks appear to be sequential based on naming."""
        title_a = task_a.title.lower()
        title_b = task_b.title.lower()

        # Look for patterns like "Step 1", "Step 2" or "Phase 1", "Phase 2"
        sequential_patterns = [
            (r'step\s*(\d+)', r'step\s*(\d+)'),
            (r'phase\s*(\d+)', r'phase\s*(\d+)'),
            (r'task\s*(\d+)', r'task\s*(\d+)'),
            (r'part\s*(\d+)', r'part\s*(\d+)'),
        ]

        for pattern_a, pattern_b in sequential_patterns:
            match_a = re.search(pattern_a, title_a)
            match_b = re.search(pattern_b, title_b)

            if match_a and match_b:
                num_a = int(match_a.group(1))
                num_b = int(match_b.group(1))
                if num_b == num_a + 1:  # Sequential
                    return True

        return False

    def _time_ranges_overlap(self, task_a: TaskNode, task_b: TaskNode) -> bool:
        """Check if two tasks have overlapping time ranges."""
        start_a = task_a.start_date
        end_a = task_a.end_date
        start_b = task_b.start_date
        end_b = task_b.end_date

        if not all([start_a, end_a, start_b, end_b]):
            return False

        # Check for overlap
        return start_a < end_b and start_b < end_a

    def _detect_cycles(self, nodes: Dict[str, TaskNode], edges: List[TaskDependency]) -> List[List[str]]:
        """Detect cycles in the dependency graph."""
        # Build adjacency list
        graph = defaultdict(list)
        for edge in edges:
            graph[edge.from_task].append(edge.to_task)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in nodes:
            if node not in visited:
                dfs(node, [])

        return cycles

    async def calculate_critical_path(self, project_id: str) -> Optional[CriticalPathResult]:
        """
        Calculate the critical path for a project.

        Args:
            project_id: Project identifier

        Returns:
            Critical path analysis result
        """
        try:
            graph = await self.build_dependency_graph(project_id)
            if not graph.nodes:
                return None

            # Find start and end nodes
            start_nodes = self._find_start_nodes(graph)
            end_nodes = self._find_end_nodes(graph)

            if not start_nodes or not end_nodes:
                return None

            # Forward pass - calculate earliest times
            earliest_start, earliest_finish = self._forward_pass(graph, start_nodes)

            # Backward pass - calculate latest times
            latest_start, latest_finish = self._backward_pass(graph, end_nodes, earliest_finish)

            # Calculate slack times
            slack_times = self._calculate_slack_times(
                graph, earliest_start, latest_start, earliest_finish, latest_finish
            )

            # Find critical path
            critical_path = self._find_critical_path(graph, slack_times)

            # Calculate total duration
            total_duration = self._calculate_path_duration(graph, critical_path)

            return CriticalPathResult(
                critical_path=critical_path,
                total_duration=total_duration,
                slack_times=slack_times,
                earliest_start=earliest_start,
                latest_start=latest_start,
                earliest_finish=earliest_finish,
                latest_finish=latest_finish
            )

        except Exception as e:
            self.logger.error(f"Error calculating critical path for project {project_id}: {e}")
            return None

    def _find_start_nodes(self, graph: DependencyGraph) -> List[str]:
        """Find nodes with no predecessors (start nodes)."""
        return [node_id for node_id, node in graph.nodes.items() if not node.predecessors]

    def _find_end_nodes(self, graph: DependencyGraph) -> List[str]:
        """Find nodes with no successors (end nodes)."""
        return [node_id for node_id, node in graph.nodes.items() if not node.successors]

    def _forward_pass(
        self,
        graph: DependencyGraph,
        start_nodes: List[str]
    ) -> Tuple[Dict[str, datetime], Dict[str, datetime]]:
        """Forward pass to calculate earliest start and finish times."""
        earliest_start = {}
        earliest_finish = {}

        # Initialize start nodes
        project_start = datetime.now()  # Use current time as project start
        for node_id in start_nodes:
            earliest_start[node_id] = project_start
            duration = graph.nodes[node_id].estimated_duration or 24  # Default 1 day
            earliest_finish[node_id] = project_start + timedelta(hours=duration)

        # Process remaining nodes in topological order
        processed = set(start_nodes)
        queue = deque(start_nodes)

        while queue:
            current_node = queue.popleft()

            for successor in graph.nodes[current_node].successors:
                if successor not in processed:
                    # Calculate earliest start for successor
                    max_predecessor_finish = max(
                        earliest_finish[pred] for pred in graph.nodes[successor].predecessors
                        if pred in earliest_finish
                    )

                    earliest_start[successor] = max_predecessor_finish
                    duration = graph.nodes[successor].estimated_duration or 24
                    earliest_finish[successor] = earliest_start[successor] + timedelta(hours=duration)

                    processed.add(successor)
                    queue.append(successor)

        return earliest_start, earliest_finish

    def _backward_pass(
        self,
        graph: DependencyGraph,
        end_nodes: List[str],
        earliest_finish: Dict[str, datetime]
    ) -> Tuple[Dict[str, datetime], Dict[str, datetime]]:
        """Backward pass to calculate latest start and finish times."""
        latest_start = {}
        latest_finish = {}

        # Initialize end nodes
        project_end = max(earliest_finish.values()) if earliest_finish else datetime.now()
        for node_id in end_nodes:
            latest_finish[node_id] = project_end
            duration = graph.nodes[node_id].estimated_duration or 24
            latest_start[node_id] = project_end - timedelta(hours=duration)

        # Process remaining nodes in reverse topological order
        processed = set(end_nodes)
        queue = deque(end_nodes)

        while queue:
            current_node = queue.popleft()

            for predecessor in graph.nodes[current_node].predecessors:
                if predecessor not in processed:
                    # Calculate latest finish for predecessor
                    min_successor_start = min(
                        latest_start[succ] for succ in graph.nodes[predecessor].successors
                        if succ in latest_start
                    )

                    latest_finish[predecessor] = min_successor_start
                    duration = graph.nodes[predecessor].estimated_duration or 24
                    latest_start[predecessor] = latest_finish[predecessor] - timedelta(hours=duration)

                    processed.add(predecessor)
                    queue.append(predecessor)

        return latest_start, latest_finish

    def _calculate_slack_times(
        self,
        graph: DependencyGraph,
        earliest_start: Dict[str, datetime],
        latest_start: Dict[str, datetime],
        earliest_finish: Dict[str, datetime],
        latest_finish: Dict[str, datetime]
    ) -> Dict[str, int]:
        """Calculate slack times for all tasks."""
        slack_times = {}

        for node_id in graph.nodes:
            if node_id in earliest_finish and node_id in latest_finish:
                slack = int((latest_finish[node_id] - earliest_finish[node_id]).total_seconds() / 3600)
                slack_times[node_id] = max(0, slack)

        return slack_times

    def _find_critical_path(self, graph: DependencyGraph, slack_times: Dict[str, int]) -> List[str]:
        """Find the critical path (tasks with zero slack)."""
        return [node_id for node_id, slack in slack_times.items() if slack == 0]

    def _calculate_path_duration(self, graph: DependencyGraph, path: List[str]) -> int:
        """Calculate total duration of a path."""
        total_duration = 0
        for node_id in path:
            duration = graph.nodes[node_id].estimated_duration or 24
            total_duration += duration
        return total_duration

    def _is_cache_valid(self, project_id: str) -> bool:
        """Check if cache entry is still valid."""
        if project_id not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[project_id]

    async def get_dependency_visualization_data(self, project_id: str) -> Dict[str, Any]:
        """
        Get data formatted for dependency visualization (e.g., for D3.js or similar).

        Returns:
            Dictionary containing nodes and edges for visualization
        """
        try:
            graph = await self.build_dependency_graph(project_id)

            # Format nodes for visualization
            nodes = []
            for node_id, node in graph.nodes.items():
                nodes.append({
                    "id": node_id,
                    "label": node.title,
                    "status": node.status,
                    "group": self._get_node_group(node),
                    "size": self._calculate_node_size(node),
                })

            # Format edges for visualization
            edges = []
            for edge in graph.edges:
                edges.append({
                    "from": edge.from_task,
                    "to": edge.to_task,
                    "type": edge.dependency_type.value,
                    "strength": edge.strength.value,
                    "label": f"{edge.dependency_type.value} ({edge.lag_time}h lag)" if edge.lag_time > 0 else edge.dependency_type.value,
                })

            return {
                "nodes": nodes,
                "edges": edges,
                "cycles": graph.cycles,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "has_cycles": len(graph.cycles) > 0,
                    "last_updated": graph.last_updated.isoformat(),
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting visualization data for project {project_id}: {e}")
            return {"nodes": [], "edges": [], "cycles": [], "metadata": {}}

    def _get_node_group(self, node: TaskNode) -> str:
        """Determine visualization group for a node."""
        status_groups = {
            "todo": "pending",
            "in_progress": "active",
            "review": "active",
            "done": "completed",
            "blocked": "blocked",
        }
        return status_groups.get(node.status, "unknown")

    def _calculate_node_size(self, node: TaskNode) -> int:
        """Calculate node size for visualization based on various factors."""
        base_size = 20

        # Size based on estimated duration
        if node.estimated_duration:
            duration_factor = min(node.estimated_duration / 40, 2)  # Cap at 2x
            base_size *= (1 + duration_factor * 0.5)

        # Size based on number of dependencies
        dependency_factor = len(node.predecessors) + len(node.successors)
        base_size *= (1 + min(dependency_factor * 0.1, 1))

        return int(base_size)

    async def analyze_impact(self, project_id: str, task_id: str, change_type: str) -> Dict[str, Any]:
        """
        Analyze the impact of a change to a task on the entire project.

        Args:
            project_id: Project identifier
            task_id: Task being changed
            change_type: Type of change (delay, deletion, etc.)

        Returns:
            Impact analysis results
        """
        try:
            graph = await self.build_dependency_graph(project_id)

            if task_id not in graph.nodes:
                return {"error": "Task not found"}

            # Get affected tasks
            affected_tasks = self._find_affected_tasks(graph, task_id)

            # Calculate impact metrics
            impact_metrics = {
                "directly_affected": len(affected_tasks["direct"]),
                "indirectly_affected": len(affected_tasks["indirect"]),
                "critical_path_affected": self._is_on_critical_path(graph, task_id),
                "estimated_delay": self._estimate_delay_impact(graph, task_id, change_type),
                "risk_level": self._calculate_risk_level(affected_tasks),
            }

            return {
                "task_id": task_id,
                "change_type": change_type,
                "affected_tasks": affected_tasks,
                "impact_metrics": impact_metrics,
                "recommendations": self._generate_impact_recommendations(impact_metrics),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing impact for task {task_id}: {e}")
            return {"error": str(e)}

    def _find_affected_tasks(self, graph: DependencyGraph, task_id: str) -> Dict[str, List[str]]:
        """Find tasks affected by a change to the given task."""
        direct_affected = []
        indirect_affected = []

        # Direct successors
        for successor in graph.nodes[task_id].successors:
            direct_affected.append(successor)

        # Indirect successors (successors of successors)
        visited = set([task_id] + direct_affected)
        queue = list(graph.nodes[task_id].successors)

        while queue:
            current = queue.pop(0)
            if current not in visited:
                visited.add(current)
                indirect_affected.append(current)

                # Add successors of current task
                for successor in graph.nodes[current].successors:
                    if successor not in visited:
                        queue.append(successor)

        return {
            "direct": direct_affected,
            "indirect": indirect_affected,
        }

    def _is_on_critical_path(self, graph: DependencyGraph, task_id: str) -> bool:
        """Check if a task is on the critical path."""
        critical_path_result = asyncio.run(self.calculate_critical_path(graph.project_id))
        if critical_path_result:
            return task_id in critical_path_result.critical_path
        return False

    def _estimate_delay_impact(self, graph: DependencyGraph, task_id: str, change_type: str) -> int:
        """Estimate the delay impact of a change."""
        # Simplified estimation - in production, this would be more sophisticated
        task_duration = graph.nodes[task_id].estimated_duration or 24

        if change_type == "delay":
            return task_duration
        elif change_type == "deletion":
            return task_duration * -1  # Negative delay (early completion)
        else:
            return 0

    def _calculate_risk_level(self, affected_tasks: Dict[str, List[str]]) -> str:
        """Calculate risk level based on affected tasks."""
        total_affected = len(affected_tasks["direct"]) + len(affected_tasks["indirect"])

        if total_affected >= 10:
            return "high"
        elif total_affected >= 5:
            return "medium"
        else:
            return "low"

    def _generate_impact_recommendations(self, impact_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []

        if impact_metrics["critical_path_affected"]:
            recommendations.append("This task is on the critical path. Changes may affect project timeline.")

        if impact_metrics["directly_affected"] > 5:
            recommendations.append("Many tasks depend on this change. Consider phased implementation.")

        if impact_metrics["risk_level"] == "high":
            recommendations.append("High risk change detected. Consider additional planning and communication.")

        if impact_metrics["estimated_delay"] > 48:  # More than 2 days
            recommendations.append("Significant delay expected. Update stakeholders and adjust deadlines.")

        return recommendations if recommendations else ["Low impact change. Proceed with standard change management."]

    async def invalidate_cache(self, project_id: str):
        """Invalidate cache for a project."""
        if project_id in self._graph_cache:
            del self._graph_cache[project_id]
        if project_id in self._cache_expiry:
            del self._cache_expiry[project_id]

        self.logger.info(f"Invalidated dependency cache for project {project_id}")


# Global service instance
task_dependency_service = TaskDependencyService()
