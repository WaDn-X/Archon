"""
Smart Task Suggestions Service

Provides intelligent task recommendations based on:
- User behavior patterns and preferences
- Project context and priorities
- Time-based analysis (optimal working hours)
- Skill matching and learning opportunities
- Task dependencies and project flow
- Team collaboration patterns
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math

from ..utils import get_enhanced_supabase_client
from .error_service import error_service
from .task_prioritization_service import task_prioritization_service


class SuggestionType(Enum):
    """Types of task suggestions."""
    NEXT_BEST_TASK = "next_best_task"
    HIGH_IMPACT = "high_impact"
    QUICK_WIN = "quick_win"
    LEARNING_OPPORTUNITY = "learning_opportunity"
    BLOCKING_TASK = "blocking_task"
    DEADLINE_DRIVEN = "deadline_driven"
    TEAM_COLLABORATION = "team_collaboration"
    MAINTENANCE_BREAK = "maintenance_break"


class SuggestionReason(Enum):
    """Reasons for task suggestions."""
    OPTIMAL_TIME = "optimal_time"
    HIGH_PRIORITY = "high_priority"
    SKILL_MATCH = "skill_match"
    DEPENDENCY_BLOCK = "dependency_block"
    TEAM_AVAILABILITY = "team_availability"
    LEARNING_GROWTH = "learning_growth"
    WORK_LIFE_BALANCE = "work_life_balance"
    PROJECT_MOMENTUM = "project_momentum"


@dataclass
class TaskSuggestion:
    """A single task suggestion with reasoning."""
    task_id: str
    suggestion_type: SuggestionType
    confidence_score: float  # 0.0 to 1.0
    reasoning: List[str]
    suggested_time: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # in minutes
    prerequisites: List[str] = field(default_factory=list)
    expected_impact: str = ""
    alternative_tasks: List[str] = field(default_factory=list)


@dataclass
class UserPattern:
    """User behavior patterns."""
    preferred_work_hours: Set[int] = field(default_factory=set)  # 0-23 hours
    preferred_work_days: Set[int] = field(default_factory=set)  # 0-6 (Monday-Sunday)
    average_task_duration: Dict[str, float] = field(default_factory=dict)  # task_type -> minutes
    common_task_types: List[str] = field(default_factory=list)
    peak_productivity_hours: Set[int] = field(default_factory=set)
    break_frequency: int = 90  # minutes between breaks
    last_break_time: Optional[datetime] = None
    skill_levels: Dict[str, float] = field(default_factory=dict)  # skill -> 0.0-1.0 proficiency
    collaboration_preference: str = "moderate"  # low, moderate, high


@dataclass
class SmartSuggestionsResult:
    """Result of smart suggestions analysis."""
    primary_suggestion: Optional[TaskSuggestion]
    alternative_suggestions: List[TaskSuggestion]
    context_analysis: Dict[str, Any]
    user_patterns: UserPattern
    project_context: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


class SmartSuggestionsService:
    """Service for generating intelligent task suggestions."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = get_enhanced_supabase_client()
        self._user_patterns_cache: Dict[str, UserPattern] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def get_smart_suggestions(
        self,
        user_id: str,
        project_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> SmartSuggestionsResult:
        """
        Generate smart task suggestions for a user in a project.

        Args:
            user_id: User identifier
            project_id: Project identifier
            context: Additional context (current time, user status, etc.)

        Returns:
            Smart suggestions result with primary and alternative suggestions
        """
        try:
            # Get user patterns
            user_patterns = await self._get_user_patterns(user_id)

            # Get project context
            project_context = await self._get_project_context(project_id, user_id)

            # Analyze current context
            context_analysis = self._analyze_current_context(context or {}, user_patterns)

            # Get available tasks
            available_tasks = await self._get_available_tasks(project_id, user_id)

            if not available_tasks:
                return SmartSuggestionsResult(
                    primary_suggestion=None,
                    alternative_suggestions=[],
                    context_analysis=context_analysis,
                    user_patterns=user_patterns,
                    project_context=project_context
                )

            # Generate suggestions
            suggestions = await self._generate_suggestions(
                available_tasks, user_patterns, project_context, context_analysis
            )

            # Sort and rank suggestions
            ranked_suggestions = self._rank_suggestions(suggestions)

            return SmartSuggestionsResult(
                primary_suggestion=ranked_suggestions[0] if ranked_suggestions else None,
                alternative_suggestions=ranked_suggestions[1:],
                context_analysis=context_analysis,
                user_patterns=user_patterns,
                project_context=project_context
            )

        except Exception as e:
            self.logger.error(f"Error generating smart suggestions for user {user_id}: {e}")
            error_service.log_error(
                "SMART_SUGGESTIONS_ERROR",
                f"Failed to generate smart suggestions for user {user_id}",
                {"user_id": user_id, "project_id": project_id, "error": str(e)}
            )

            # Return empty result on error
            return SmartSuggestionsResult(
                primary_suggestion=None,
                alternative_suggestions=[],
                context_analysis={},
                user_patterns=UserPattern(),
                project_context={}
            )

    async def _get_user_patterns(self, user_id: str) -> UserPattern:
        """Get or build user behavior patterns."""
        # Check cache first
        if user_id in self._user_patterns_cache and self._is_cache_valid(user_id):
            return self._user_patterns_cache[user_id]

        try:
            # Fetch user activity data
            activities = await self._fetch_user_activities(user_id)

            # Analyze patterns
            patterns = self._analyze_user_patterns(activities)

            # Cache the result
            self._user_patterns_cache[user_id] = patterns
            self._cache_expiry[user_id] = datetime.now() + timedelta(hours=2)

            return patterns

        except Exception as e:
            self.logger.warning(f"Error getting user patterns for {user_id}: {e}")
            return UserPattern()

    async def _fetch_user_activities(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user activity data for pattern analysis."""
        try:
            # This would query user activity logs
            # For now, return mock data based on typical patterns
            return [
                {
                    "task_type": "feature",
                    "start_time": "09:00",
                    "duration": 120,
                    "day_of_week": 1,  # Monday
                    "completed": True,
                },
                {
                    "task_type": "bug",
                    "start_time": "14:00",
                    "duration": 45,
                    "day_of_week": 2,
                    "completed": True,
                },
                # More activity data...
            ]
        except Exception as e:
            self.logger.warning(f"Error fetching user activities: {e}")
            return []

    def _analyze_user_patterns(self, activities: List[Dict[str, Any]]) -> UserPattern:
        """Analyze user activities to build behavior patterns."""
        if not activities:
            return UserPattern()

        patterns = UserPattern()

        # Analyze work hours
        work_hours = defaultdict(int)
        work_days = defaultdict(int)
        task_durations = defaultdict(list)
        task_types = defaultdict(int)

        for activity in activities:
            # Work hours
            hour = int(activity["start_time"].split(":")[0])
            work_hours[hour] += 1

            # Work days
            work_days[activity["day_of_week"]] += 1

            # Task durations
            task_durations[activity["task_type"]].append(activity["duration"])

            # Task types
            task_types[activity["task_type"]] += 1

        # Set preferred work hours (top 3 most common)
        top_hours = sorted(work_hours.items(), key=lambda x: x[1], reverse=True)[:3]
        patterns.preferred_work_hours = {hour for hour, _ in top_hours}

        # Set preferred work days
        top_days = sorted(work_days.items(), key=lambda x: x[1], reverse=True)[:3]
        patterns.preferred_work_days = {day for day, _ in top_days}

        # Calculate average task durations
        for task_type, durations in task_durations.items():
            patterns.average_task_duration[task_type] = sum(durations) / len(durations)

        # Set common task types
        patterns.common_task_types = [
            task_type for task_type, _ in
            sorted(task_types.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

        # Identify peak productivity hours
        peak_threshold = max(work_hours.values()) * 0.8 if work_hours else 0
        patterns.peak_productivity_hours = {
            hour for hour, count in work_hours.items() if count >= peak_threshold
        }

        return patterns

    async def _get_project_context(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Get project context and user's role in it."""
        try:
            # Fetch project information
            project_info = await self._fetch_project_info(project_id)

            # Get user's assigned tasks
            user_tasks = await self._fetch_user_tasks(project_id, user_id)

            # Analyze project status
            project_status = self._analyze_project_status(project_info, user_tasks)

            return {
                "project_info": project_info,
                "user_tasks": user_tasks,
                "project_status": project_status,
                "team_members": await self._get_team_members(project_id),
                "upcoming_deadlines": await self._get_upcoming_deadlines(project_id),
                "blocking_tasks": await self._get_blocking_tasks(project_id, user_id),
            }

        except Exception as e:
            self.logger.warning(f"Error getting project context: {e}")
            return {}

    async def _fetch_project_info(self, project_id: str) -> Dict[str, Any]:
        """Fetch basic project information."""
        try:
            # Mock project info - in production, fetch from database
            return {
                "id": project_id,
                "name": "Sample Project",
                "status": "active",
                "priority": "high",
                "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
                "completion_percentage": 65,
            }
        except Exception:
            return {}

    async def _fetch_user_tasks(self, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Fetch tasks assigned to the user."""
        try:
            response = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={
                    "project_id": project_id,
                    "assignee": user_id,
                    "status": ["todo", "in_progress"]
                }
            )
            return response.get("data", [])
        except Exception:
            return []

    def _analyze_project_status(self, project_info: Dict[str, Any], user_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze project status and user's contribution."""
        total_tasks = len(user_tasks)
        completed_tasks = len([t for t in user_tasks if t.get("status") == "completed"])
        overdue_tasks = len([t for t in user_tasks if self._is_overdue(t)])

        return {
            "user_completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "overdue_tasks_count": overdue_tasks,
            "project_progress": project_info.get("completion_percentage", 0),
            "time_pressure": self._calculate_time_pressure(project_info),
        }

    def _is_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if a task is overdue."""
        due_date = task.get("due_date")
        if not due_date:
            return False

        try:
            due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            return datetime.now() > due_datetime
        except Exception:
            return False

    def _calculate_time_pressure(self, project_info: Dict[str, Any]) -> str:
        """Calculate time pressure level for the project."""
        deadline = project_info.get("deadline")
        if not deadline:
            return "low"

        try:
            deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            days_remaining = (deadline_date - datetime.now()).days

            if days_remaining < 3:
                return "critical"
            elif days_remaining < 7:
                return "high"
            elif days_remaining < 14:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"

    async def _get_team_members(self, project_id: str) -> List[Dict[str, Any]]:
        """Get team members for the project."""
        try:
            # Mock team members
            return [
                {"id": "user1", "name": "Alice", "role": "developer", "status": "online"},
                {"id": "user2", "name": "Bob", "role": "designer", "status": "away"},
            ]
        except Exception:
            return []

    async def _get_upcoming_deadlines(self, project_id: str) -> List[Dict[str, Any]]:
        """Get upcoming deadlines for the project."""
        try:
            # Mock deadlines
            return [
                {"task_id": "task1", "title": "Release v1.0", "due_date": (datetime.now() + timedelta(days=5)).isoformat()},
                {"task_id": "task2", "title": "Design Review", "due_date": (datetime.now() + timedelta(days=2)).isoformat()},
            ]
        except Exception:
            return []

    async def _get_blocking_tasks(self, project_id: str, user_id: str) -> List[str]:
        """Get tasks that are blocking other work."""
        try:
            # This would analyze dependencies to find blocking tasks
            return ["task1", "task3"]  # Mock blocking tasks
        except Exception:
            return []

    def _analyze_current_context(
        self,
        context: Dict[str, Any],
        user_patterns: UserPattern
    ) -> Dict[str, Any]:
        """Analyze current user context for suggestions."""
        now = context.get("current_time", datetime.now())
        current_hour = now.hour
        current_day = now.weekday()  # 0 = Monday

        # Check if current time is optimal for work
        is_optimal_time = (
            current_hour in user_patterns.preferred_work_hours and
            current_day in user_patterns.preferred_work_days
        )

        # Check recent activity patterns
        recent_breaks_needed = self._check_break_needed(user_patterns, now)

        # Check energy levels (based on time of day)
        energy_level = self._estimate_energy_level(current_hour)

        return {
            "current_hour": current_hour,
            "current_day": current_day,
            "is_optimal_time": is_optimal_time,
            "breaks_needed": recent_breaks_needed,
            "energy_level": energy_level,
            "time_until_next_break": self._calculate_time_until_break(user_patterns, now),
        }

    def _check_break_needed(self, patterns: UserPattern, current_time: datetime) -> bool:
        """Check if user needs a break based on patterns."""
        if not patterns.last_break_time:
            return False

        time_since_last_break = current_time - patterns.last_break_time
        return time_since_last_break.total_seconds() / 60 >= patterns.break_frequency

    def _estimate_energy_level(self, hour: int) -> str:
        """Estimate energy level based on time of day."""
        if 9 <= hour <= 11:
            return "high"
        elif 14 <= hour <= 16:
            return "high"
        elif 12 <= hour <= 13 or 17 <= hour <= 18:
            return "medium"
        else:
            return "low"

    def _calculate_time_until_break(self, patterns: UserPattern, current_time: datetime) -> Optional[int]:
        """Calculate minutes until next break is recommended."""
        if not patterns.last_break_time:
            return patterns.break_frequency

        time_since_last_break = current_time - patterns.last_break_time
        minutes_since = time_since_last_break.total_seconds() / 60

        if minutes_since >= patterns.break_frequency:
            return 0  # Break needed now

        return int(patterns.break_frequency - minutes_since)

    async def _get_available_tasks(self, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get tasks available for the user to work on."""
        try:
            # Get user's assigned tasks that are not completed
            user_tasks = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={
                    "project_id": project_id,
                    "assignee": user_id,
                    "status": ["todo", "in_progress"]
                }
            )

            # Also get unassigned tasks that could be picked up
            unassigned_tasks = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={
                    "project_id": project_id,
                    "assignee": {"$is": None},
                    "status": "todo"
                },
                limit=5
            )

            all_tasks = user_tasks.get("data", []) + unassigned_tasks.get("data", [])
            return all_tasks

        except Exception as e:
            self.logger.error(f"Error getting available tasks: {e}")
            return []

    async def _generate_suggestions(
        self,
        tasks: List[Dict[str, Any]],
        user_patterns: UserPattern,
        project_context: Dict[str, Any],
        context_analysis: Dict[str, Any]
    ) -> List[TaskSuggestion]:
        """Generate task suggestions based on all available data."""
        suggestions = []

        for task in tasks:
            # Generate different types of suggestions
            suggestions.extend(await self._generate_task_suggestions(
                task, user_patterns, project_context, context_analysis
            ))

        return suggestions

    async def _generate_task_suggestions(
        self,
        task: Dict[str, Any],
        user_patterns: UserPattern,
        project_context: Dict[str, Any],
        context_analysis: Dict[str, Any]
    ) -> List[TaskSuggestion]:
        """Generate suggestions for a specific task."""
        suggestions = []
        task_id = task["id"]

        # 1. Next Best Task Suggestion
        next_best_score = await self._calculate_next_best_score(
            task, user_patterns, project_context, context_analysis
        )
        if next_best_score > 0.7:
            suggestions.append(TaskSuggestion(
                task_id=task_id,
                suggestion_type=SuggestionType.NEXT_BEST_TASK,
                confidence_score=next_best_score,
                reasoning=self._generate_next_best_reasoning(task, user_patterns, context_analysis),
                suggested_time=self._calculate_optimal_start_time(task, user_patterns),
                estimated_duration=self._estimate_task_duration(task, user_patterns),
                expected_impact="High impact on project progress"
            ))

        # 2. Quick Win Suggestion
        if self._is_quick_win(task, user_patterns):
            suggestions.append(TaskSuggestion(
                task_id=task_id,
                suggestion_type=SuggestionType.QUICK_WIN,
                confidence_score=0.8,
                reasoning=["Quick task that can be completed in one sitting", "Provides immediate progress feedback"],
                estimated_duration=self._estimate_task_duration(task, user_patterns),
                expected_impact="Fast completion with visible progress"
            ))

        # 3. Learning Opportunity Suggestion
        learning_score = self._calculate_learning_score(task, user_patterns)
        if learning_score > 0.6:
            suggestions.append(TaskSuggestion(
                task_id=task_id,
                suggestion_type=SuggestionType.LEARNING_OPPORTUNITY,
                confidence_score=learning_score,
                reasoning=["Great opportunity to develop new skills", "Aligns with your learning goals"],
                expected_impact="Skill development and growth"
            ))

        # 4. Blocking Task Suggestion
        if self._is_blocking_task(task, project_context):
            suggestions.append(TaskSuggestion(
                task_id=task_id,
                suggestion_type=SuggestionType.BLOCKING_TASK,
                confidence_score=0.9,
                reasoning=["This task is blocking other work", "High priority to unblock team progress"],
                expected_impact="Unblocks multiple dependent tasks"
            ))

        # 5. Deadline Driven Suggestion
        if self._is_deadline_driven(task):
            suggestions.append(TaskSuggestion(
                task_id=task_id,
                suggestion_type=SuggestionType.DEADLINE_DRIVEN,
                confidence_score=0.85,
                reasoning=["Approaching deadline requires immediate attention"],
                suggested_time=datetime.now(),
                expected_impact="Prevents deadline slippage"
            ))

        return suggestions

    async def _calculate_next_best_score(
        self,
        task: Dict[str, Any],
        user_patterns: UserPattern,
        project_context: Dict[str, Any],
        context_analysis: Dict[str, Any]
    ) -> float:
        """Calculate score for next best task recommendation."""
        score = 0.5  # Base score

        # Time alignment bonus
        if context_analysis.get("is_optimal_time"):
            score += 0.2

        # Skill match bonus
        task_type = task.get("type", "")
        if task_type in user_patterns.common_task_types:
            score += 0.15

        # Energy level alignment
        energy_level = context_analysis.get("energy_level", "medium")
        task_complexity = task.get("complexity", "medium")

        if (energy_level == "high" and task_complexity in ["high", "medium"]) or \
           (energy_level == "medium" and task_complexity == "medium") or \
           (energy_level == "low" and task_complexity == "low"):
            score += 0.1

        # Project priority bonus
        project_status = project_context.get("project_status", {})
        if project_status.get("time_pressure") in ["high", "critical"]:
            score += 0.15

        return min(1.0, score)

    def _generate_next_best_reasoning(
        self,
        task: Dict[str, Any],
        user_patterns: UserPattern,
        context_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate reasoning for next best task suggestion."""
        reasoning = []

        if context_analysis.get("is_optimal_time"):
            reasoning.append("Current time aligns with your most productive hours")

        task_type = task.get("type", "")
        if task_type in user_patterns.common_task_types:
            reasoning.append(f"Matches your experience with {task_type} tasks")

        if context_analysis.get("energy_level") == "high":
            reasoning.append("Your current energy level is optimal for this task")

        return reasoning if reasoning else ["Well-balanced task for current context"]

    def _calculate_optimal_start_time(
        self,
        task: Dict[str, Any],
        user_patterns: UserPattern
    ) -> Optional[datetime]:
        """Calculate optimal start time for a task."""
        if not user_patterns.peak_productivity_hours:
            return None

        # Find next available peak hour
        current_hour = datetime.now().hour
        peak_hours = sorted(user_patterns.peak_productivity_hours)

        for hour in peak_hours:
            if hour > current_hour:
                next_peak = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
                return next_peak

        # If no peak hour today, use first peak hour tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        first_peak = min(peak_hours)
        return tomorrow.replace(hour=first_peak, minute=0, second=0, microsecond=0)

    def _estimate_task_duration(self, task: Dict[str, Any], user_patterns: UserPattern) -> Optional[int]:
        """Estimate task duration based on user patterns."""
        task_type = task.get("type", "")

        if task_type in user_patterns.average_task_duration:
            return int(user_patterns.average_task_duration[task_type])

        # Default estimates based on task type
        default_estimates = {
            "bug": 45,
            "feature": 120,
            "documentation": 60,
            "review": 30,
            "meeting": 60,
        }

        return default_estimates.get(task_type, 90)  # Default 90 minutes

    def _is_quick_win(self, task: Dict[str, Any], user_patterns: UserPattern) -> bool:
        """Determine if a task is a quick win."""
        estimated_duration = self._estimate_task_duration(task, user_patterns)
        return estimated_duration is not None and estimated_duration <= 60  # 1 hour or less

    def _calculate_learning_score(self, task: Dict[str, Any], user_patterns: UserPattern) -> float:
        """Calculate learning opportunity score."""
        task_skills = set(task.get("required_skills", []))
        user_skills = set(user_patterns.skill_levels.keys())

        new_skills = task_skills - user_skills
        familiar_skills = task_skills & user_skills

        if not task_skills:
            return 0.0

        # Mix of familiar and new skills is ideal for learning
        learning_ratio = len(new_skills) / len(task_skills)

        if 0.3 <= learning_ratio <= 0.7:  # 30-70% new skills
            return 0.8
        elif learning_ratio > 0.7:  # Mostly new skills
            return 0.6
        else:  # Mostly familiar skills
            return 0.2

    def _is_blocking_task(self, task: Dict[str, Any], project_context: Dict[str, Any]) -> bool:
        """Check if task is blocking other work."""
        blocking_tasks = project_context.get("blocking_tasks", [])
        return task["id"] in blocking_tasks

    def _is_deadline_driven(self, task: Dict[str, Any]) -> bool:
        """Check if task is deadline driven."""
        due_date = task.get("due_date")
        if not due_date:
            return False

        try:
            due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            hours_until_due = (due_datetime - datetime.now()).total_seconds() / 3600
            return hours_until_due <= 24  # Due within 24 hours
        except Exception:
            return False

    def _rank_suggestions(self, suggestions: List[TaskSuggestion]) -> List[TaskSuggestion]:
        """Rank suggestions by confidence score and other factors."""
        return sorted(
            suggestions,
            key=lambda s: (
                s.confidence_score,  # Primary: confidence score
                self._get_suggestion_priority(s.suggestion_type),  # Secondary: suggestion type priority
                -(s.estimated_duration or 0)  # Tertiary: prefer shorter tasks (negative for ascending sort)
            ),
            reverse=True
        )

    def _get_suggestion_priority(self, suggestion_type: SuggestionType) -> int:
        """Get priority weight for suggestion types."""
        priorities = {
            SuggestionType.BLOCKING_TASK: 10,
            SuggestionType.DEADLINE_DRIVEN: 9,
            SuggestionType.NEXT_BEST_TASK: 8,
            SuggestionType.QUICK_WIN: 7,
            SuggestionType.LEARNING_OPPORTUNITY: 6,
            SuggestionType.TEAM_COLLABORATION: 5,
            SuggestionType.MAINTENANCE_BREAK: 1,
        }
        return priorities.get(suggestion_type, 5)

    def _is_cache_valid(self, user_id: str) -> bool:
        """Check if cache entry is still valid."""
        if user_id not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[user_id]


# Global service instance
smart_suggestions_service = SmartSuggestionsService()
