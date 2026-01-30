"""
Time Tracking Service

Provides comprehensive time tracking functionality for tasks and projects including:
- Time logging and session management
- Time analytics and reporting
- Productivity metrics and insights
- Time estimation vs actual tracking
- Team time allocation analysis
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics


@dataclass
class TimeEntry:
    """Individual time tracking entry."""
    id: str
    task_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    description: str = ""
    category: str = "development"  # development, testing, review, planning, etc.
    is_billable: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TimeSession:
    """Active time tracking session."""
    id: str
    task_id: str
    user_id: str
    start_time: datetime
    description: str = ""
    category: str = "development"


@dataclass
class TimeAnalytics:
    """Time tracking analytics for tasks and projects."""
    total_time_minutes: int
    average_session_minutes: float
    longest_session_minutes: int
    shortest_session_minutes: int
    sessions_count: int
    productivity_score: float  # 0-100 based on consistency and focus
    time_by_category: Dict[str, int]
    time_by_day: Dict[str, int]
    estimated_vs_actual_ratio: float


@dataclass
class ProjectTimeSummary:
    """Time summary for a complete project."""
    project_id: str
    total_time_minutes: int
    average_time_per_task: float
    most_time_consuming_tasks: List[str]
    team_productivity_trends: Dict[str, List[float]]
    milestone_achievements: Dict[str, datetime]
    budget_utilization: float


class TimeTrackingService:
    """Service for comprehensive time tracking and analytics."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_sessions: Dict[str, TimeSession] = {}  # user_id -> session
        self.time_entries: Dict[str, List[TimeEntry]] = {}  # task_id -> entries

    async def start_time_session(
        self,
        task_id: str,
        user_id: str,
        description: str = "",
        category: str = "development"
    ) -> str:
        """
        Start a time tracking session for a task.

        Args:
            task_id: Task to track time for
            user_id: User starting the session
            description: Optional description of work being done
            category: Work category (development, testing, review, etc.)

        Returns:
            Session ID
        """
        try:
            # Check if user already has an active session
            if user_id in self.active_sessions:
                await self.stop_time_session(user_id)

            # Create new session
            session_id = f"session_{user_id}_{datetime.now().isoformat()}"
            session = TimeSession(
                id=session_id,
                task_id=task_id,
                user_id=user_id,
                start_time=datetime.now(),
                description=description,
                category=category
            )

            self.active_sessions[user_id] = session

            self.logger.info(f"Started time session for task {task_id} by user {user_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Error starting time session: {e}")
            raise

    async def stop_time_session(self, user_id: str) -> Optional[TimeEntry]:
        """
        Stop an active time session and create a time entry.

        Args:
            user_id: User whose session to stop

        Returns:
            Created time entry or None if no active session
        """
        try:
            session = self.active_sessions.get(user_id)
            if not session:
                return None

            # Calculate duration
            end_time = datetime.now()
            duration_minutes = int((end_time - session.start_time).total_seconds() / 60)

            # Create time entry
            entry_id = f"entry_{session.task_id}_{end_time.isoformat()}"
            time_entry = TimeEntry(
                id=entry_id,
                task_id=session.task_id,
                user_id=user_id,
                start_time=session.start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                description=session.description,
                category=session.category,
                is_billable=True
            )

            # Store time entry
            if session.task_id not in self.time_entries:
                self.time_entries[session.task_id] = []
            self.time_entries[session.task_id].append(time_entry)

            # Remove active session
            del self.active_sessions[user_id]

            self.logger.info(f"Stopped time session for task {session.task_id}: {duration_minutes} minutes")
            return time_entry

        except Exception as e:
            self.logger.error(f"Error stopping time session: {e}")
            return None

    async def add_manual_time_entry(
        self,
        task_id: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        category: str = "development"
    ) -> str:
        """
        Add a manual time entry (for time worked without active session).

        Args:
            task_id: Task the time was spent on
            user_id: User who worked the time
            start_time: When work started
            end_time: When work ended
            description: Description of work done
            category: Work category

        Returns:
            Entry ID
        """
        try:
            duration_minutes = int((end_time - start_time).total_seconds() / 60)

            entry_id = f"manual_{task_id}_{end_time.isoformat()}"
            time_entry = TimeEntry(
                id=entry_id,
                task_id=task_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                description=description,
                category=category,
                is_billable=True
            )

            # Store time entry
            if task_id not in self.time_entries:
                self.time_entries[task_id] = []
            self.time_entries[task_id].append(time_entry)

            self.logger.info(f"Added manual time entry for task {task_id}: {duration_minutes} minutes")
            return entry_id

        except Exception as e:
            self.logger.error(f"Error adding manual time entry: {e}")
            raise

    async def get_task_time_analytics(self, task_id: str) -> TimeAnalytics:
        """Get comprehensive time analytics for a task."""
        try:
            entries = self.time_entries.get(task_id, [])

            if not entries:
                return TimeAnalytics(
                    total_time_minutes=0,
                    average_session_minutes=0,
                    longest_session_minutes=0,
                    shortest_session_minutes=0,
                    sessions_count=0,
                    productivity_score=0,
                    time_by_category={},
                    time_by_day={},
                    estimated_vs_actual_ratio=0
                )

            # Calculate basic metrics
            durations = [entry.duration_minutes for entry in entries if entry.duration_minutes]
            total_time = sum(durations)

            # Time by category
            time_by_category = {}
            for entry in entries:
                category = entry.category
                time_by_category[category] = time_by_category.get(category, 0) + entry.duration_minutes

            # Time by day
            time_by_day = {}
            for entry in entries:
                day = entry.start_time.strftime("%Y-%m-%d")
                time_by_day[day] = time_by_day.get(day, 0) + entry.duration_minutes

            # Productivity score (based on session consistency)
            if durations:
                avg_duration = statistics.mean(durations)
                std_duration = statistics.stdev(durations) if len(durations) > 1 else 0

                # Lower standard deviation = more consistent = higher productivity
                consistency_score = max(0, 100 - (std_duration / avg_duration * 100)) if avg_duration > 0 else 0

                # Session frequency (more sessions = more focused work)
                days_with_sessions = len(set(entry.start_time.strftime("%Y-%m-%d") for entry in entries))
                frequency_score = min(100, days_with_sessions * 20)

                productivity_score = (consistency_score * 0.7) + (frequency_score * 0.3)
            else:
                productivity_score = 0

            return TimeAnalytics(
                total_time_minutes=total_time,
                average_session_minutes=statistics.mean(durations) if durations else 0,
                longest_session_minutes=max(durations) if durations else 0,
                shortest_session_minutes=min(durations) if durations else 0,
                sessions_count=len(entries),
                productivity_score=productivity_score,
                time_by_category=time_by_category,
                time_by_day=time_by_day,
                estimated_vs_actual_ratio=0  # Would compare with task estimates
            )

        except Exception as e:
            self.logger.error(f"Error getting task time analytics: {e}")
            return TimeAnalytics(
                total_time_minutes=0,
                average_session_minutes=0,
                longest_session_minutes=0,
                shortest_session_minutes=0,
                sessions_count=0,
                productivity_score=0,
                time_by_category={},
                time_by_day={},
                estimated_vs_actual_ratio=0
            )

    async def get_project_time_summary(self, project_id: str, tasks: List[Dict[str, Any]]) -> ProjectTimeSummary:
        """Get time summary for all tasks in a project."""
        try:
            total_time = 0
            task_times = {}

            # Calculate time for each task
            for task in tasks:
                task_id = task['id']
                analytics = await self.get_task_time_analytics(task_id)
                task_time = analytics.total_time_minutes
                task_times[task_id] = task_time
                total_time += task_time

            # Find most time-consuming tasks
            sorted_tasks = sorted(task_times.items(), key=lambda x: x[1], reverse=True)
            most_time_consuming = [task_id for task_id, _ in sorted_tasks[:5]]

            # Calculate average time per task
            avg_time_per_task = total_time / len(tasks) if tasks else 0

            return ProjectTimeSummary(
                project_id=project_id,
                total_time_minutes=total_time,
                average_time_per_task=avg_time_per_task,
                most_time_consuming_tasks=most_time_consuming,
                team_productivity_trends={},  # Would analyze team trends over time
                milestone_achievements={},   # Would track milestone completions
                budget_utilization=0          # Would compare with project budget
            )

        except Exception as e:
            self.logger.error(f"Error getting project time summary: {e}")
            return ProjectTimeSummary(
                project_id=project_id,
                total_time_minutes=0,
                average_time_per_task=0,
                most_time_consuming_tasks=[],
                team_productivity_trends={},
                milestone_achievements={},
                budget_utilization=0
            )

    async def get_user_time_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get time summary for a user within a date range."""
        try:
            user_entries = []

            # Find all entries for this user
            for task_entries in self.time_entries.values():
                for entry in task_entries:
                    if entry.user_id == user_id and start_date <= entry.start_time <= end_date:
                        user_entries.append(entry)

            if not user_entries:
                return {
                    "total_time_minutes": 0,
                    "sessions_count": 0,
                    "average_session_minutes": 0,
                    "categories_breakdown": {},
                    "daily_breakdown": {},
                    "productivity_trends": []
                }

            # Calculate metrics
            total_time = sum(entry.duration_minutes for entry in user_entries)
            sessions_count = len(user_entries)

            # Categories breakdown
            categories_breakdown = {}
            for entry in user_entries:
                category = entry.category
                categories_breakdown[category] = categories_breakdown.get(category, 0) + entry.duration_minutes

            # Daily breakdown
            daily_breakdown = {}
            for entry in user_entries:
                day = entry.start_time.strftime("%Y-%m-%d")
                daily_breakdown[day] = daily_breakdown.get(day, 0) + entry.duration_minutes

            # Productivity trends (simplified)
            productivity_trends = []
            for entry in user_entries:
                # Simple productivity score based on session length and category
                base_score = 50
                if entry.duration_minutes > 60:  # Longer sessions = more focused
                    base_score += 20
                if entry.category in ["development", "testing"]:
                    base_score += 15
                productivity_trends.append(min(100, base_score))

            return {
                "total_time_minutes": total_time,
                "sessions_count": sessions_count,
                "average_session_minutes": total_time / sessions_count if sessions_count > 0 else 0,
                "categories_breakdown": categories_breakdown,
                "daily_breakdown": daily_breakdown,
                "productivity_trends": productivity_trends
            }

        except Exception as e:
            self.logger.error(f"Error getting user time summary: {e}")
            return {
                "total_time_minutes": 0,
                "sessions_count": 0,
                "average_session_minutes": 0,
                "categories_breakdown": {},
                "daily_breakdown": {},
                "productivity_trends": []
            }

    async def get_time_tracking_report(
        self,
        project_id: str,
        user_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Generate comprehensive time tracking report."""
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()

            report = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "project_summary": {},
                "user_summaries": {},
                "productivity_insights": [],
                "recommendations": []
            }

            # Get project summary
            # In production, this would query the database for tasks
            mock_tasks = [
                {"id": "task_1", "title": "Setup database"},
                {"id": "task_2", "title": "Implement API"},
                {"id": "task_3", "title": "Create frontend"}
            ]

            project_summary = await self.get_project_time_summary(project_id, mock_tasks)
            report["project_summary"] = {
                "total_time_minutes": project_summary.total_time_minutes,
                "average_time_per_task": project_summary.average_time_per_task,
                "most_time_consuming_tasks": project_summary.most_time_consuming_tasks
            }

            # Get user summaries
            if user_id:
                user_summary = await self.get_user_time_summary(user_id, start_date, end_date)
                report["user_summaries"][user_id] = user_summary

            # Generate productivity insights
            total_sessions = sum(user["sessions_count"] for user in report["user_summaries"].values())
            total_time = sum(user["total_time_minutes"] for user in report["user_summaries"].values())

            if total_sessions > 0:
                avg_session_time = total_time / total_sessions
                report["productivity_insights"].append(
                    f"Average session time: {avg_session_time:.1f} minutes"
                )

            # Generate recommendations
            if avg_session_time > 90:
                report["recommendations"].append(
                    "Consider shorter, more focused work sessions for better productivity"
                )
            elif avg_session_time < 15:
                report["recommendations"].append(
                    "Consider longer work sessions to reduce context switching overhead"
                )

            return report

        except Exception as e:
            self.logger.error(f"Error generating time tracking report: {e}")
            return {
                "error": str(e),
                "period": {},
                "project_summary": {},
                "user_summaries": {},
                "productivity_insights": [],
                "recommendations": []
            }

    def get_active_sessions(self) -> Dict[str, TimeSession]:
        """Get all currently active time sessions."""
        return self.active_sessions.copy()

    def get_session_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a user's active session."""
        session = self.active_sessions.get(user_id)
        if not session:
            return None

        current_duration = int((datetime.now() - session.start_time).total_seconds() / 60)

        return {
            "session_id": session.id,
            "task_id": session.task_id,
            "start_time": session.start_time.isoformat(),
            "current_duration_minutes": current_duration,
            "description": session.description,
            "category": session.category
        }


# Global instance
time_tracking_service = TimeTrackingService()
