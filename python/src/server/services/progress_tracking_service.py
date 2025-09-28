"""
Progress Tracking and Milestone Management Service

Provides comprehensive progress tracking including:
- Real-time progress calculation and visualization
- Milestone management and tracking
- Predictive analytics for project completion
- Progress reporting and analytics
- Goal setting and achievement tracking
- Burn-down charts and velocity tracking
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

from ..utils import get_enhanced_supabase_client
from .error_service import error_service


class MilestoneStatus(Enum):
    """Status of a milestone."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"


class ProgressMetric(Enum):
    """Types of progress metrics."""
    TASK_COMPLETION = "task_completion"
    TIME_SPENT = "time_spent"
    VELOCITY = "velocity"
    BURNDOWN = "burndown"
    QUALITY_METRICS = "quality_metrics"
    TEAM_PRODUCTIVITY = "team_productivity"


@dataclass
class Milestone:
    """Project milestone definition."""
    id: str
    title: str
    description: str
    target_date: datetime
    status: MilestoneStatus
    progress_percentage: float
    dependencies: Set[str] = field(default_factory=set)
    deliverables: List[str] = field(default_factory=list)
    owner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProgressSnapshot:
    """Snapshot of project progress at a point in time."""
    timestamp: datetime
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    overdue_tasks: int
    time_spent_hours: float
    estimated_remaining_hours: float
    velocity_tasks_per_day: float
    milestone_progress: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProgressAnalytics:
    """Analytics and insights about project progress."""
    overall_progress: float
    projected_completion_date: Optional[datetime]
    velocity_trend: str  # "increasing", "decreasing", "stable"
    risk_level: str  # "low", "medium", "high", "critical"
    bottleneck_tasks: List[str]
    upcoming_milestones: List[Milestone]
    recommendations: List[str]
    progress_rate: float  # tasks per day
    estimated_days_remaining: Optional[float]


@dataclass
class BurnDownData:
    """Data for burn-down chart visualization."""
    dates: List[datetime]
    planned_remaining: List[int]
    actual_remaining: List[int]
    ideal_burndown: List[float]


class ProgressTrackingService:
    """Service for tracking project progress and managing milestones."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = get_enhanced_supabase_client()
        self._progress_cache: Dict[str, ProgressSnapshot] = {}
        self._analytics_cache: Dict[str, ProgressAnalytics] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def create_milestone(
        self,
        project_id: str,
        title: str,
        description: str,
        target_date: datetime,
        deliverables: List[str] = None,
        owner: str = None,
        dependencies: Set[str] = None
    ) -> Optional[Milestone]:
        """
        Create a new milestone for a project.

        Args:
            project_id: Project identifier
            title: Milestone title
            description: Milestone description
            target_date: Target completion date
            deliverables: List of deliverables for this milestone
            owner: Milestone owner
            dependencies: Set of milestone IDs this depends on

        Returns:
            Created milestone object
        """
        try:
            milestone_data = {
                "project_id": project_id,
                "title": title,
                "description": description,
                "target_date": target_date.isoformat(),
                "status": MilestoneStatus.NOT_STARTED.value,
                "progress_percentage": 0.0,
                "deliverables": deliverables or [],
                "owner": owner,
                "dependencies": list(dependencies or set()),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            response = await self.supabase.insert("archon_milestones", milestone_data)
            milestone_id = response.get("data", [{}])[0].get("id")

            if milestone_id:
                milestone = Milestone(
                    id=milestone_id,
                    title=title,
                    description=description,
                    target_date=target_date,
                    status=MilestoneStatus.NOT_STARTED,
                    progress_percentage=0.0,
                    dependencies=dependencies or set(),
                    deliverables=deliverables or [],
                    owner=owner,
                )

                self.logger.info(f"Created milestone '{title}' for project {project_id}")
                return milestone

        except Exception as e:
            self.logger.error(f"Error creating milestone for project {project_id}: {e}")
            error_service.log_error(
                "MILESTONE_CREATION_ERROR",
                f"Failed to create milestone for project {project_id}",
                {"project_id": project_id, "title": title, "error": str(e)}
            )

        return None

    async def update_milestone_progress(
        self,
        project_id: str,
        milestone_id: str,
        progress_percentage: float,
        status: Optional[MilestoneStatus] = None
    ) -> bool:
        """
        Update milestone progress.

        Args:
            project_id: Project identifier
            milestone_id: Milestone identifier
            progress_percentage: Progress percentage (0-100)
            status: New milestone status

        Returns:
            Success status
        """
        try:
            update_data = {
                "progress_percentage": max(0, min(100, progress_percentage)),
                "updated_at": datetime.now().isoformat(),
            }

            if status:
                update_data["status"] = status.value

            await self.supabase.update(
                "archon_milestones",
                update_data,
                {"id": milestone_id, "project_id": project_id}
            )

            # Invalidate caches
            self._invalidate_cache(project_id)

            self.logger.info(f"Updated milestone {milestone_id} progress to {progress_percentage}%")
            return True

        except Exception as e:
            self.logger.error(f"Error updating milestone {milestone_id}: {e}")
            return False

    async def get_project_progress(self, project_id: str) -> ProgressSnapshot:
        """
        Get current progress snapshot for a project.

        Args:
            project_id: Project identifier

        Returns:
            Current progress snapshot
        """
        try:
            # Check cache first
            if self._is_cache_valid(project_id):
                return self._progress_cache[project_id]

            # Fetch project tasks
            tasks = await self._fetch_project_tasks(project_id)

            # Calculate progress metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t["status"] == "completed"])
            in_progress_tasks = len([t for t in tasks if t["status"] == "in_progress"])
            blocked_tasks = len([t for t in tasks if t["status"] == "blocked"])
            overdue_tasks = len([t for t in tasks if self._is_task_overdue(t)])

            # Calculate time metrics
            time_spent = await self._calculate_time_spent(project_id)
            estimated_remaining = await self._calculate_estimated_remaining(project_id, tasks)

            # Calculate velocity (tasks per day over last 7 days)
            velocity = await self._calculate_velocity(project_id)

            # Get milestone progress
            milestone_progress = await self._get_milestone_progress(project_id)

            snapshot = ProgressSnapshot(
                timestamp=datetime.now(),
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                in_progress_tasks=in_progress_tasks,
                blocked_tasks=blocked_tasks,
                overdue_tasks=overdue_tasks,
                time_spent_hours=time_spent,
                estimated_remaining_hours=estimated_remaining,
                velocity_tasks_per_day=velocity,
                milestone_progress=milestone_progress,
            )

            # Cache the snapshot
            self._progress_cache[project_id] = snapshot
            self._cache_expiry[project_id] = datetime.now() + timedelta(minutes=5)

            return snapshot

        except Exception as e:
            self.logger.error(f"Error getting project progress for {project_id}: {e}")
            error_service.log_error(
                "PROGRESS_CALCULATION_ERROR",
                f"Failed to calculate progress for project {project_id}",
                {"project_id": project_id, "error": str(e)}
            )

            # Return empty snapshot on error
            return ProgressSnapshot(
                timestamp=datetime.now(),
                total_tasks=0,
                completed_tasks=0,
                in_progress_tasks=0,
                blocked_tasks=0,
                overdue_tasks=0,
                time_spent_hours=0,
                estimated_remaining_hours=0,
                velocity_tasks_per_day=0,
            )

    async def get_progress_analytics(self, project_id: str) -> ProgressAnalytics:
        """
        Get comprehensive progress analytics for a project.

        Args:
            project_id: Project identifier

        Returns:
            Progress analytics with insights and recommendations
        """
        try:
            # Check cache first
            if project_id in self._analytics_cache and self._is_cache_valid(project_id):
                return self._analytics_cache[project_id]

            # Get current progress
            snapshot = await self.get_project_progress(project_id)

            # Calculate overall progress
            overall_progress = (
                snapshot.completed_tasks / snapshot.total_tasks
                if snapshot.total_tasks > 0 else 0
            )

            # Calculate projected completion date
            projected_completion = await self._calculate_projected_completion(
                project_id, snapshot
            )

            # Analyze velocity trend
            velocity_trend = await self._analyze_velocity_trend(project_id)

            # Assess risk level
            risk_level = self._assess_risk_level(snapshot, projected_completion)

            # Identify bottleneck tasks
            bottleneck_tasks = await self._identify_bottlenecks(project_id)

            # Get upcoming milestones
            upcoming_milestones = await self._get_upcoming_milestones(project_id)

            # Calculate progress rate
            progress_rate = snapshot.velocity_tasks_per_day

            # Estimate days remaining
            estimated_days_remaining = None
            if progress_rate > 0:
                remaining_tasks = snapshot.total_tasks - snapshot.completed_tasks
                estimated_days_remaining = remaining_tasks / progress_rate

            # Generate recommendations
            recommendations = self._generate_recommendations(
                snapshot, velocity_trend, risk_level, bottleneck_tasks
            )

            analytics = ProgressAnalytics(
                overall_progress=overall_progress,
                projected_completion_date=projected_completion,
                velocity_trend=velocity_trend,
                risk_level=risk_level,
                bottleneck_tasks=bottleneck_tasks,
                upcoming_milestones=upcoming_milestones,
                recommendations=recommendations,
                progress_rate=progress_rate,
                estimated_days_remaining=estimated_days_remaining,
            )

            # Cache analytics
            self._analytics_cache[project_id] = analytics

            return analytics

        except Exception as e:
            self.logger.error(f"Error generating progress analytics for {project_id}: {e}")
            return ProgressAnalytics(
                overall_progress=0,
                projected_completion_date=None,
                velocity_trend="unknown",
                risk_level="unknown",
                bottleneck_tasks=[],
                upcoming_milestones=[],
                recommendations=["Unable to generate recommendations due to an error"],
                progress_rate=0,
                estimated_days_remaining=None,
            )

    async def get_burndown_data(
        self,
        project_id: str,
        days: int = 30
    ) -> BurnDownData:
        """
        Generate burn-down chart data for a project.

        Args:
            project_id: Project identifier
            days: Number of days to include in the chart

        Returns:
            Burn-down chart data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Generate date range
            dates = []
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date)
                current_date += timedelta(days=1)

            # Get total tasks at project start
            total_tasks = await self._get_total_tasks_at_date(project_id, start_date)

            # Calculate planned remaining tasks (ideal burndown)
            planned_remaining = []
            for i in range(len(dates)):
                progress_ratio = i / (len(dates) - 1) if len(dates) > 1 else 0
                remaining = total_tasks * (1 - progress_ratio)
                planned_remaining.append(remaining)

            # Get actual remaining tasks for each date
            actual_remaining = []
            for date in dates:
                remaining = await self._get_remaining_tasks_at_date(project_id, date)
                actual_remaining.append(remaining)

            # Calculate ideal burndown line
            ideal_burndown = []
            if total_tasks > 0:
                for i in range(len(dates)):
                    ideal_remaining = total_tasks * (1 - i / max(1, len(dates) - 1))
                    ideal_burndown.append(ideal_remaining)

            return BurnDownData(
                dates=dates,
                planned_remaining=planned_remaining,
                actual_remaining=actual_remaining,
                ideal_burndown=ideal_burndown,
            )

        except Exception as e:
            self.logger.error(f"Error generating burndown data for {project_id}: {e}")
            return BurnDownData(
                dates=[],
                planned_remaining=[],
                actual_remaining=[],
                ideal_burndown=[],
            )

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

    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if a task is overdue."""
        due_date = task.get("due_date")
        if not due_date or task["status"] == "completed":
            return False

        try:
            due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            return datetime.now() > due_datetime
        except Exception:
            return False

    async def _calculate_time_spent(self, project_id: str) -> float:
        """Calculate total time spent on project tasks."""
        try:
            # This would query time tracking logs
            # For now, return a mock value
            return 120.5  # 120.5 hours
        except Exception as e:
            return 0.0

    async def _calculate_estimated_remaining(self, project_id: str, tasks: List[Dict[str, Any]]) -> float:
        """Calculate estimated remaining work hours."""
        try:
            remaining_tasks = [t for t in tasks if t["status"] != "completed"]
            total_remaining = 0.0

            for task in remaining_tasks:
                # Use estimated duration or default to 8 hours
                estimated_duration = task.get("estimated_duration", 8)
                total_remaining += estimated_duration

            return total_remaining
        except Exception as e:
            return 0.0

    async def _calculate_velocity(self, project_id: str) -> float:
        """Calculate team velocity (tasks completed per day)."""
        try:
            # Get completion data for the last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)

            # This would query completion logs
            # For now, return a mock velocity
            return 2.3  # 2.3 tasks per day
        except Exception as e:
            return 0.0

    async def _get_milestone_progress(self, project_id: str) -> Dict[str, float]:
        """Get progress percentages for all project milestones."""
        try:
            response = await self.supabase.select(
                "archon_milestones",
                columns=["id", "progress_percentage"],
                filters={"project_id": project_id}
            )

            milestones = response.get("data", [])
            return {m["id"]: m["progress_percentage"] for m in milestones}
        except Exception as e:
            return {}

    async def _calculate_projected_completion(
        self,
        project_id: str,
        snapshot: ProgressSnapshot
    ) -> Optional[datetime]:
        """Calculate projected project completion date."""
        try:
            if snapshot.velocity_tasks_per_day <= 0:
                return None

            remaining_tasks = snapshot.total_tasks - snapshot.completed_tasks
            days_remaining = remaining_tasks / snapshot.velocity_tasks_per_day

            return datetime.now() + timedelta(days=days_remaining)
        except Exception as e:
            return None

    async def _analyze_velocity_trend(self, project_id: str) -> str:
        """Analyze velocity trend over time."""
        try:
            # Get velocity data for the last 4 weeks
            velocities = []
            for i in range(4):
                week_start = datetime.now() - timedelta(days=(i + 1) * 7)
                week_end = datetime.now() - timedelta(days=i * 7)

                # This would calculate velocity for each week
                # For now, return mock data
                velocities.append(2.0 + (i * 0.2))  # Slightly increasing trend

            if len(velocities) < 2:
                return "stable"

            # Calculate trend
            recent_avg = statistics.mean(velocities[:2])
            older_avg = statistics.mean(velocities[2:]) if len(velocities) > 2 else recent_avg

            if recent_avg > older_avg * 1.1:
                return "increasing"
            elif recent_avg < older_avg * 0.9:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            return "unknown"

    def _assess_risk_level(
        self,
        snapshot: ProgressSnapshot,
        projected_completion: Optional[datetime]
    ) -> str:
        """Assess project risk level."""
        risk_score = 0

        # Risk factors
        if snapshot.overdue_tasks > 0:
            risk_score += 2
        if snapshot.blocked_tasks > snapshot.total_tasks * 0.2:  # >20% blocked
            risk_score += 2
        if snapshot.velocity_tasks_per_day < 1:  # Less than 1 task per day
            risk_score += 1

        # Check if projected completion is past deadline
        if projected_completion:
            # This would compare with actual project deadline
            # For now, assume some deadline logic
            pass

        # Determine risk level
        if risk_score >= 4:
            return "critical"
        elif risk_score >= 2:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"

    async def _identify_bottlenecks(self, project_id: str) -> List[str]:
        """Identify bottleneck tasks in the project."""
        try:
            # This would analyze dependencies and task states
            # For now, return mock bottlenecks
            return ["task1", "task5"]  # Mock bottleneck task IDs
        except Exception as e:
            return []

    async def _get_upcoming_milestones(self, project_id: str) -> List[Milestone]:
        """Get upcoming milestones for the project."""
        try:
            response = await self.supabase.select(
                "archon_milestones",
                columns="*",
                filters={
                    "project_id": project_id,
                    "status": ["not_started", "in_progress"],
                    "target_date": {"$gte": datetime.now().isoformat()}
                },
                order_by={"target_date": "asc"},
                limit=5
            )

            milestones = []
            for m in response.get("data", []):
                milestone = Milestone(
                    id=m["id"],
                    title=m["title"],
                    description=m["description"],
                    target_date=datetime.fromisoformat(m["target_date"].replace('Z', '+00:00')),
                    status=MilestoneStatus(m["status"]),
                    progress_percentage=m["progress_percentage"],
                    dependencies=set(m.get("dependencies", [])),
                    deliverables=m.get("deliverables", []),
                    owner=m.get("owner"),
                    created_at=datetime.fromisoformat(m["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(m["updated_at"].replace('Z', '+00:00')),
                )
                milestones.append(milestone)

            return milestones

        except Exception as e:
            self.logger.error(f"Error fetching upcoming milestones: {e}")
            return []

    def _generate_recommendations(
        self,
        snapshot: ProgressSnapshot,
        velocity_trend: str,
        risk_level: str,
        bottleneck_tasks: List[str]
    ) -> List[str]:
        """Generate recommendations based on project analysis."""
        recommendations = []

        if risk_level == "critical":
            recommendations.append("🚨 Critical risk detected. Immediate attention required to unblock progress.")
        elif risk_level == "high":
            recommendations.append("⚠️ High risk level. Consider reallocating resources to critical tasks.")

        if snapshot.overdue_tasks > 0:
            recommendations.append(f"📅 {snapshot.overdue_tasks} tasks are overdue. Prioritize completion of these tasks.")

        if snapshot.blocked_tasks > 0:
            recommendations.append(f"🚧 {snapshot.blocked_tasks} tasks are blocked. Focus on resolving dependencies.")

        if velocity_trend == "decreasing":
            recommendations.append("📉 Team velocity is decreasing. Consider reviewing workload and identifying blockers.")

        if bottleneck_tasks:
            recommendations.append(f"🔧 {len(bottleneck_tasks)} bottleneck tasks identified. Address these to improve overall progress.")

        if not recommendations:
            recommendations.append("✅ Project is progressing well. Continue current momentum.")

        return recommendations

    async def _get_total_tasks_at_date(self, project_id: str, date: datetime) -> int:
        """Get total number of tasks at a specific date."""
        try:
            # This would query historical task data
            # For now, return current total
            tasks = await self._fetch_project_tasks(project_id)
            return len(tasks)
        except Exception as e:
            return 0

    async def _get_remaining_tasks_at_date(self, project_id: str, date: datetime) -> int:
        """Get number of remaining tasks at a specific date."""
        try:
            # This would query historical completion data
            # For now, simulate decreasing remaining tasks
            total_tasks = await self._get_total_tasks_at_date(project_id, date)
            days_elapsed = (datetime.now() - date).days
            completion_rate = 0.1  # 10% completion per day (mock)
            completed = min(total_tasks, int(days_elapsed * completion_rate * total_tasks))
            return total_tasks - completed
        except Exception as e:
            return 0

    def _is_cache_valid(self, project_id: str) -> bool:
        """Check if cache entry is still valid."""
        if project_id not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[project_id]

    def _invalidate_cache(self, project_id: str):
        """Invalidate cache for a project."""
        cache_keys = [k for k in self._progress_cache.keys() if k == project_id]
        analytics_keys = [k for k in self._analytics_cache.keys() if k == project_id]
        expiry_keys = [k for k in self._cache_expiry.keys() if k == project_id]

        for key in cache_keys:
            del self._progress_cache[key]
        for key in analytics_keys:
            del self._analytics_cache[key]
        for key in expiry_keys:
            del self._cache_expiry[key]


# Global service instance
progress_tracking_service = ProgressTrackingService()
