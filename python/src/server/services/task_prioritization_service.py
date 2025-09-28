"""
Intelligent Task Prioritization Service

Provides AI-powered task scoring, prioritization, and optimization
based on multiple factors including urgency, importance, dependencies,
user patterns, and project context.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from ..utils import get_enhanced_supabase_client
from .error_service import error_service


class PriorityLevel(Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKLOG = "backlog"


class UrgencyLevel(Enum):
    """Task urgency levels."""
    IMMEDIATE = "immediate"
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    FLEXIBLE = "flexible"


@dataclass
class TaskFactors:
    """Factors influencing task priority."""
    deadline_weight: float = 0.3
    dependency_weight: float = 0.25
    user_pattern_weight: float = 0.2
    project_context_weight: float = 0.15
    complexity_weight: float = 0.1

    def validate(self) -> bool:
        """Validate that weights sum to 1.0."""
        total = sum([
            self.deadline_weight,
            self.dependency_weight,
            self.user_pattern_weight,
            self.project_context_weight,
            self.complexity_weight
        ])
        return abs(total - 1.0) < 0.01


@dataclass
class TaskScore:
    """Comprehensive task scoring result."""
    task_id: str
    total_score: float
    priority_level: PriorityLevel
    urgency_level: UrgencyLevel
    deadline_score: float
    dependency_score: float
    user_pattern_score: float
    project_context_score: float
    complexity_score: float
    recommended_position: int
    reasoning: List[str] = field(default_factory=list)


@dataclass
class TaskDependency:
    """Task dependency information."""
    task_id: str
    depends_on: Set[str] = field(default_factory=set)
    blocks: Set[str] = field(default_factory=set)
    dependency_type: str = "finish_to_start"  # finish_to_start, start_to_start, etc.


class TaskPrioritizationService:
    """AI-powered task prioritization service."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = get_enhanced_supabase_client()
        self.factors = TaskFactors()

        # Cache for user patterns and project context
        self._user_pattern_cache: Dict[str, Dict[str, Any]] = {}
        self._project_context_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def prioritize_tasks(
        self,
        project_id: str,
        user_id: str,
        task_ids: Optional[List[str]] = None
    ) -> List[TaskScore]:
        """
        Prioritize tasks for a project using AI-powered scoring.

        Args:
            project_id: Project identifier
            user_id: User identifier for pattern analysis
            task_ids: Optional list of specific task IDs to prioritize

        Returns:
            List of task scores ordered by priority
        """
        try:
            # Fetch tasks
            tasks = await self._fetch_tasks(project_id, task_ids)
            if not tasks:
                return []

            # Analyze dependencies
            dependencies = await self._analyze_dependencies(tasks)

            # Score each task
            task_scores = []
            for task in tasks:
                score = await self._calculate_task_score(
                    task, user_id, project_id, dependencies
                )
                task_scores.append(score)

            # Sort by total score (highest first)
            task_scores.sort(key=lambda x: x.total_score, reverse=True)

            # Assign recommended positions
            for i, score in enumerate(task_scores):
                score.recommended_position = i + 1

            self.logger.info(f"Prioritized {len(task_scores)} tasks for project {project_id}")
            return task_scores

        except Exception as e:
            self.logger.error(f"Error prioritizing tasks: {e}")
            error_service.log_error(
                "TASK_PRIORITIZATION_ERROR",
                f"Failed to prioritize tasks for project {project_id}",
                {"project_id": project_id, "user_id": user_id, "error": str(e)}
            )
            return []

    async def _fetch_tasks(
        self,
        project_id: str,
        task_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch tasks from database."""
        try:
            if task_ids:
                # Fetch specific tasks
                response = await self.supabase.select(
                    "archon_tasks",
                    columns="*",
                    filters={"project_id": project_id, "id": task_ids}
                )
            else:
                # Fetch all active tasks for project
                response = await self.supabase.select(
                    "archon_tasks",
                    columns="*",
                    filters={"project_id": project_id, "status": ["todo", "in_progress"]}
                )

            return response.get("data", [])
        except Exception as e:
            self.logger.error(f"Error fetching tasks: {e}")
            return []

    async def _analyze_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, TaskDependency]:
        """Analyze task dependencies."""
        dependencies: Dict[str, TaskDependency] = {}

        for task in tasks:
            task_id = task["id"]
            dependency = TaskDependency(task_id=task_id)

            # Check for explicit dependencies (if stored in task data)
            if "depends_on" in task and task["depends_on"]:
                dependency.depends_on = set(task["depends_on"])

            # Check for blocking relationships
            for other_task in tasks:
                if other_task["id"] != task_id:
                    # Simple dependency detection based on task relationships
                    if self._detect_dependency(task, other_task):
                        dependency.depends_on.add(other_task["id"])

            dependencies[task_id] = dependency

        return dependencies

    def _detect_dependency(self, task: Dict[str, Any], other_task: Dict[str, Any]) -> bool:
        """Detect if task depends on other_task."""
        # This is a simplified dependency detection
        # In production, this would be more sophisticated

        # Check if other_task is mentioned in task description
        if other_task.get("title", "").lower() in task.get("description", "").lower():
            return True

        # Check if they share similar keywords (simplified NLP)
        task_keywords = set(task.get("title", "").lower().split())
        other_keywords = set(other_task.get("title", "").lower().split())

        if task_keywords & other_keywords:  # Intersection
            return True

        return False

    async def _calculate_task_score(
        self,
        task: Dict[str, Any],
        user_id: str,
        project_id: str,
        dependencies: Dict[str, TaskDependency]
    ) -> TaskScore:
        """Calculate comprehensive score for a task."""
        task_id = task["id"]

        # Calculate individual scores
        deadline_score = await self._calculate_deadline_score(task)
        dependency_score = self._calculate_dependency_score(task_id, dependencies)
        user_pattern_score = await self._calculate_user_pattern_score(task, user_id)
        project_context_score = await self._calculate_project_context_score(task, project_id)
        complexity_score = self._calculate_complexity_score(task)

        # Calculate weighted total score
        total_score = (
            self.factors.deadline_weight * deadline_score +
            self.factors.dependency_weight * dependency_score +
            self.factors.user_pattern_weight * user_pattern_score +
            self.factors.project_context_weight * project_context_score +
            self.factors.complexity_weight * complexity_score
        )

        # Determine priority and urgency levels
        priority_level = self._determine_priority_level(total_score)
        urgency_level = self._determine_urgency_level(task, deadline_score)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            task, deadline_score, dependency_score, user_pattern_score,
            project_context_score, complexity_score
        )

        return TaskScore(
            task_id=task_id,
            total_score=total_score,
            priority_level=priority_level,
            urgency_level=urgency_level,
            deadline_score=deadline_score,
            dependency_score=dependency_score,
            user_pattern_score=user_pattern_score,
            project_context_score=project_context_score,
            complexity_score=complexity_score,
            recommended_position=0,  # Will be set later
            reasoning=reasoning
        )

    async def _calculate_deadline_score(self, task: Dict[str, Any]) -> float:
        """Calculate score based on deadline urgency."""
        deadline = task.get("due_date")
        if not deadline:
            return 0.2  # Low urgency for tasks without deadlines

        try:
            if isinstance(deadline, str):
                deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            else:
                deadline_date = deadline

            now = datetime.now()
            days_until_deadline = (deadline_date - now).days

            if days_until_deadline < 0:
                return 1.0  # Overdue - highest urgency
            elif days_until_deadline == 0:
                return 0.9  # Due today
            elif days_until_deadline <= 1:
                return 0.8  # Due tomorrow
            elif days_until_deadline <= 3:
                return 0.7  # Due this week
            elif days_until_deadline <= 7:
                return 0.5  # Due next week
            elif days_until_deadline <= 14:
                return 0.3  # Due in two weeks
            else:
                return 0.1  # Due later

        except Exception as e:
            self.logger.warning(f"Error calculating deadline score: {e}")
            return 0.2

    def _calculate_dependency_score(self, task_id: str, dependencies: Dict[str, TaskDependency]) -> float:
        """Calculate score based on dependency relationships."""
        if task_id not in dependencies:
            return 0.5

        dependency = dependencies[task_id]

        # Tasks with many dependencies get higher priority
        dependency_count = len(dependency.depends_on) + len(dependency.blocks)

        if dependency_count == 0:
            return 0.3  # Independent tasks
        elif dependency_count <= 2:
            return 0.6  # Some dependencies
        elif dependency_count <= 5:
            return 0.8  # Many dependencies
        else:
            return 1.0  # Highly dependent task

    async def _calculate_user_pattern_score(self, task: Dict[str, Any], user_id: str) -> float:
        """Calculate score based on user behavior patterns."""
        try:
            # Check cache first
            cache_key = f"user_pattern_{user_id}"
            if self._is_cache_valid(cache_key):
                patterns = self._user_pattern_cache.get(cache_key, {})
            else:
                # Fetch user patterns from database
                patterns = await self._fetch_user_patterns(user_id)
                self._user_pattern_cache[cache_key] = patterns
                self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)

            # Analyze task against user patterns
            score = 0.5  # Default

            # Check task type preferences
            task_type = task.get("type", "").lower()
            if task_type in patterns.get("preferred_task_types", []):
                score += 0.2

            # Check time preferences
            current_hour = datetime.now().hour
            preferred_hours = patterns.get("preferred_work_hours", [])
            if preferred_hours and current_hour in preferred_hours:
                score += 0.1

            # Check completion patterns
            similar_tasks = patterns.get("completed_similar_tasks", 0)
            if similar_tasks > 0:
                score += min(0.2, similar_tasks * 0.05)

            return min(1.0, score)

        except Exception as e:
            self.logger.warning(f"Error calculating user pattern score: {e}")
            return 0.5

    async def _calculate_project_context_score(self, task: Dict[str, Any], project_id: str) -> float:
        """Calculate score based on project context."""
        try:
            # Check cache first
            cache_key = f"project_context_{project_id}"
            if self._is_cache_valid(cache_key):
                context = self._project_context_cache.get(cache_key, {})
            else:
                # Fetch project context
                context = await self._fetch_project_context(project_id)
                self._project_context_cache[cache_key] = context
                self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=2)

            score = 0.5  # Default

            # Check if task aligns with project priorities
            task_tags = set(task.get("tags", []))
            project_priorities = set(context.get("priority_tags", []))
            if task_tags & project_priorities:
                score += 0.2

            # Check project phase alignment
            task_phase = task.get("phase", "").lower()
            project_phase = context.get("current_phase", "").lower()
            if task_phase == project_phase:
                score += 0.15

            # Check resource availability
            required_resources = task.get("required_resources", [])
            available_resources = context.get("available_resources", [])
            if all(resource in available_resources for resource in required_resources):
                score += 0.15

            return min(1.0, score)

        except Exception as e:
            self.logger.warning(f"Error calculating project context score: {e}")
            return 0.5

    def _calculate_complexity_score(self, task: Dict[str, Any]) -> float:
        """Calculate score based on task complexity."""
        complexity_indicators = 0

        # Check description length (longer = more complex)
        description = task.get("description", "")
        if len(description) > 500:
            complexity_indicators += 1
        elif len(description) > 200:
            complexity_indicators += 0.5

        # Check for subtasks
        if task.get("subtasks") and len(task["subtasks"]) > 3:
            complexity_indicators += 1

        # Check for multiple assignees
        if task.get("assignees") and len(task["assignees"]) > 1:
            complexity_indicators += 0.5

        # Check for technical requirements
        if task.get("technical_requirements") and len(task["technical_requirements"]) > 2:
            complexity_indicators += 1

        # Check for attachments/links
        if task.get("attachments") and len(task["attachments"]) > 3:
            complexity_indicators += 0.5

        # Convert to score (0-1 scale)
        if complexity_indicators >= 4:
            return 1.0  # Very complex
        elif complexity_indicators >= 2:
            return 0.7  # Moderately complex
        elif complexity_indicators >= 1:
            return 0.5  # Somewhat complex
        else:
            return 0.2  # Simple task

    def _determine_priority_level(self, total_score: float) -> PriorityLevel:
        """Determine priority level from total score."""
        if total_score >= 0.8:
            return PriorityLevel.CRITICAL
        elif total_score >= 0.6:
            return PriorityLevel.HIGH
        elif total_score >= 0.4:
            return PriorityLevel.MEDIUM
        elif total_score >= 0.2:
            return PriorityLevel.LOW
        else:
            return PriorityLevel.BACKLOG

    def _determine_urgency_level(self, task: Dict[str, Any], deadline_score: float) -> UrgencyLevel:
        """Determine urgency level based on deadline and task characteristics."""
        if deadline_score >= 0.9:
            return UrgencyLevel.IMMEDIATE
        elif deadline_score >= 0.7:
            return UrgencyLevel.TODAY
        elif deadline_score >= 0.5:
            return UrgencyLevel.THIS_WEEK
        elif deadline_score >= 0.3:
            return UrgencyLevel.THIS_MONTH
        else:
            return UrgencyLevel.FLEXIBLE

    def _generate_reasoning(
        self,
        task: Dict[str, Any],
        deadline_score: float,
        dependency_score: float,
        user_pattern_score: float,
        project_context_score: float,
        complexity_score: float
    ) -> List[str]:
        """Generate human-readable reasoning for task prioritization."""
        reasoning = []

        if deadline_score >= 0.8:
            reasoning.append("High urgency due to approaching deadline")
        elif deadline_score <= 0.3:
            reasoning.append("Low urgency - flexible timeline")

        if dependency_score >= 0.7:
            reasoning.append("High dependency impact - blocks multiple other tasks")
        elif dependency_score <= 0.3:
            reasoning.append("Low dependency impact - can be worked on independently")

        if user_pattern_score >= 0.7:
            reasoning.append("Aligns with your work patterns and preferences")
        elif user_pattern_score <= 0.3:
            reasoning.append("May not align with your typical work patterns")

        if project_context_score >= 0.7:
            reasoning.append("High priority for current project phase")
        elif project_context_score <= 0.3:
            reasoning.append("Lower priority for current project context")

        if complexity_score >= 0.7:
            reasoning.append("High complexity - requires focused attention")
        elif complexity_score <= 0.3:
            reasoning.append("Lower complexity - good for quick wins")

        return reasoning if reasoning else ["Standard prioritization based on multiple factors"]

    async def _fetch_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Fetch user behavior patterns from database."""
        try:
            # This would typically query user analytics/history
            # For now, return default patterns
            return {
                "preferred_task_types": ["feature", "bug", "documentation"],
                "preferred_work_hours": [9, 10, 11, 14, 15, 16],
                "completed_similar_tasks": 5,
                "average_task_completion_time": 2.5,  # hours
            }
        except Exception as e:
            self.logger.warning(f"Error fetching user patterns: {e}")
            return {}

    async def _fetch_project_context(self, project_id: str) -> Dict[str, Any]:
        """Fetch project context information."""
        try:
            # This would query project metadata
            # For now, return default context
            return {
                "current_phase": "development",
                "priority_tags": ["urgent", "critical", "high-priority"],
                "available_resources": ["developer", "designer", "tester"],
                "project_status": "active",
            }
        except Exception as e:
            self.logger.warning(f"Error fetching project context: {e}")
            return {}

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    async def update_factors(self, new_factors: TaskFactors) -> bool:
        """Update prioritization factors."""
        if not new_factors.validate():
            error_service.log_error(
                "INVALID_PRIORITIZATION_FACTORS",
                "Task prioritization factors must sum to 1.0",
                {"factors": new_factors.__dict__}
            )
            return False

        self.factors = new_factors

        # Clear caches to force recalculation
        self._user_pattern_cache.clear()
        self._project_context_cache.clear()
        self._cache_expiry.clear()

        self.logger.info("Updated task prioritization factors")
        return True

    async def get_task_recommendations(
        self,
        user_id: str,
        project_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get personalized task recommendations for a user.

        Args:
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of recommendations

        Returns:
            List of recommended tasks with reasoning
        """
        try:
            # Get all tasks for project
            tasks = await self._fetch_tasks(project_id)

            if not tasks:
                return []

            # Score and sort tasks
            task_scores = await self.prioritize_tasks(project_id, user_id)

            # Convert to recommendation format
            recommendations = []
            for score in task_scores[:limit]:
                task = next((t for t in tasks if t["id"] == score.task_id), None)
                if task:
                    recommendations.append({
                        "task": task,
                        "score": score.total_score,
                        "priority": score.priority_level.value,
                        "urgency": score.urgency_level.value,
                        "reasoning": score.reasoning,
                        "position": score.recommended_position,
                    })

            return recommendations

        except Exception as e:
            self.logger.error(f"Error getting task recommendations: {e}")
            return []


# Global service instance
task_prioritization_service = TaskPrioritizationService()
