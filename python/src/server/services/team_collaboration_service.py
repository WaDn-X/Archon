"""
Team Collaboration Service

Provides comprehensive team collaboration features including:
- Team management and member roles
- Intelligent task assignment and workload balancing
- Collaboration analytics and insights
- Team communication and coordination
- Resource allocation and capacity planning
- Cross-functional team support
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
from .task_prioritization_service import task_prioritization_service


class TeamRole(Enum):
    """Team member roles."""
    OWNER = "owner"
    MANAGER = "manager"
    LEAD = "lead"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    QA = "qa"
    ANALYST = "analyst"
    STAKEHOLDER = "stakeholder"


class TaskAssignmentStrategy(Enum):
    """Strategies for task assignment."""
    ROUND_ROBIN = "round_robin"
    WORKLOAD_BALANCE = "workload_balance"
    SKILL_BASED = "skill_based"
    AVAILABILITY_BASED = "availability_based"
    PRIORITY_BASED = "priority_based"


@dataclass
class TeamMember:
    """Team member information."""
    user_id: str
    username: str
    email: str
    role: TeamRole
    skills: Set[str] = field(default_factory=set)
    availability_hours_per_week: int = 40
    current_workload: int = 0  # Number of active tasks
    capacity_utilization: float = 0.0  # 0.0 to 1.0
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)


@dataclass
class WorkloadAnalysis:
    """Analysis of team workload distribution."""
    total_members: int
    average_workload: float
    workload_distribution: Dict[str, int]  # user_id -> task_count
    overloaded_members: List[str]
    underutilized_members: List[str]
    capacity_utilization: Dict[str, float]
    recommendations: List[str]


@dataclass
class Team:
    """Team information and configuration."""
    id: str
    name: str
    description: str
    project_id: str
    members: Dict[str, TeamMember] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAssignment:
    """Task assignment details."""
    task_id: str
    assignee_id: str
    assigned_by: str
    assigned_at: datetime
    estimated_hours: Optional[int] = None
    priority: str = "medium"
    reason: str = ""


@dataclass
class CollaborationMetrics:
    """Metrics for team collaboration effectiveness."""
    communication_frequency: float
    task_completion_rate: float
    average_response_time: float
    cross_team_collaboration: float
    knowledge_sharing: float
    conflict_resolution: float


class TeamCollaborationService:
    """Service for managing team collaboration and task assignment."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = get_enhanced_supabase_client()
        self._team_cache: Dict[str, Team] = {}
        self._workload_cache: Dict[str, WorkloadAnalysis] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def create_team(
        self,
        name: str,
        description: str,
        project_id: str,
        owner_id: str
    ) -> Optional[Team]:
        """
        Create a new team for a project.

        Args:
            name: Team name
            description: Team description
            project_id: Associated project ID
            owner_id: Team owner user ID

        Returns:
            Created team object
        """
        try:
            team_data = {
                "name": name,
                "description": description,
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
                "settings": {
                    "default_assignment_strategy": TaskAssignmentStrategy.WORKLOAD_BALANCE.value,
                    "max_tasks_per_member": 5,
                    "auto_assignment_enabled": True,
                }
            }

            response = await self.supabase.insert("archon_teams", team_data)
            team_id = response.get("data", [{}])[0].get("id")

            if team_id:
                # Add owner as first member
                await self.add_team_member(team_id, owner_id, TeamRole.OWNER)

                team = Team(
                    id=team_id,
                    name=name,
                    description=description,
                    project_id=project_id,
                )

                # Add owner to team
                owner = await self._get_user_info(owner_id)
                if owner:
                    team.members[owner_id] = TeamMember(
                        user_id=owner_id,
                        username=owner["username"],
                        email=owner["email"],
                        role=TeamRole.OWNER,
                    )

                self.logger.info(f"Created team '{name}' for project {project_id}")
                return team

        except Exception as e:
            self.logger.error(f"Error creating team for project {project_id}: {e}")
            error_service.log_error(
                "TEAM_CREATION_ERROR",
                f"Failed to create team for project {project_id}",
                {"project_id": project_id, "name": name, "error": str(e)}
            )

        return None

    async def add_team_member(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole,
        skills: Set[str] = None
    ) -> bool:
        """
        Add a member to a team.

        Args:
            team_id: Team identifier
            user_id: User identifier
            role: Team role for the member
            skills: Set of member skills

        Returns:
            Success status
        """
        try:
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return False

            member_data = {
                "team_id": team_id,
                "user_id": user_id,
                "role": role.value,
                "skills": list(skills or set()),
                "joined_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
            }

            await self.supabase.insert("archon_team_members", member_data)

            # Invalidate cache
            self._invalidate_cache(team_id)

            self.logger.info(f"Added user {user_id} to team {team_id} as {role.value}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding member {user_id} to team {team_id}: {e}")
            return False

    async def assign_task(
        self,
        task_id: str,
        assignee_id: str,
        assigned_by: str,
        project_id: str,
        strategy: TaskAssignmentStrategy = None
    ) -> Optional[TaskAssignment]:
        """
        Assign a task to a team member.

        Args:
            task_id: Task identifier
            assignee_id: User ID to assign the task to
            assigned_by: User ID who made the assignment
            project_id: Project identifier
            strategy: Assignment strategy to use

        Returns:
            Task assignment object
        """
        try:
            # Get task information
            task = await self._get_task_info(task_id)
            if not task:
                return None

            # Use specified strategy or default
            if not strategy:
                team_settings = await self._get_team_settings(project_id)
                strategy = TaskAssignmentStrategy(team_settings.get("default_assignment_strategy", "workload_balance"))

            # Validate assignment
            if not await self._validate_assignment(task_id, assignee_id, project_id):
                return None

            assignment_data = {
                "task_id": task_id,
                "assignee_id": assignee_id,
                "assigned_by": assigned_by,
                "assigned_at": datetime.now().isoformat(),
                "estimated_hours": task.get("estimated_duration"),
                "strategy": strategy.value,
            }

            await self.supabase.insert("archon_task_assignments", assignment_data)

            # Update task assignee
            await self.supabase.update(
                "archon_tasks",
                {"assignee": assignee_id, "assigned_at": datetime.now().isoformat()},
                {"id": task_id}
            )

            assignment = TaskAssignment(
                task_id=task_id,
                assignee_id=assignee_id,
                assigned_by=assigned_by,
                assigned_at=datetime.now(),
                estimated_hours=task.get("estimated_duration"),
            )

            # Notify team via real-time collaboration
            await self._notify_assignment(assignment, project_id)

            self.logger.info(f"Assigned task {task_id} to user {assignee_id}")
            return assignment

        except Exception as e:
            self.logger.error(f"Error assigning task {task_id}: {e}")
            return None

    async def auto_assign_tasks(
        self,
        project_id: str,
        tasks: List[str] = None,
        strategy: TaskAssignmentStrategy = None
    ) -> Dict[str, str]:
        """
        Automatically assign tasks using intelligent algorithms.

        Args:
            project_id: Project identifier
            tasks: List of task IDs to assign (optional)
            strategy: Assignment strategy to use

        Returns:
            Dictionary mapping task_id to assignee_id
        """
        try:
            # Get unassigned tasks
            if tasks:
                unassigned_tasks = await self._get_tasks_by_ids(tasks)
            else:
                unassigned_tasks = await self._get_unassigned_tasks(project_id)

            if not unassigned_tasks:
                return {}

            # Get team members
            team_members = await self._get_team_members(project_id)
            if not team_members:
                return {}

            # Use specified strategy or default
            if not strategy:
                team_settings = await self._get_team_settings(project_id)
                strategy = TaskAssignmentStrategy(team_settings.get("default_assignment_strategy", "workload_balance"))

            # Apply assignment strategy
            assignments = await self._apply_assignment_strategy(
                unassigned_tasks, team_members, strategy
            )

            # Execute assignments
            assignment_results = {}
            for task_id, assignee_id in assignments.items():
                assignment = await self.assign_task(
                    task_id, assignee_id, "system", project_id, strategy
                )
                if assignment:
                    assignment_results[task_id] = assignee_id

            self.logger.info(f"Auto-assigned {len(assignment_results)} tasks using {strategy.value} strategy")
            return assignment_results

        except Exception as e:
            self.logger.error(f"Error in auto-assignment for project {project_id}: {e}")
            return {}

    async def analyze_workload(self, project_id: str) -> WorkloadAnalysis:
        """
        Analyze team workload distribution.

        Args:
            project_id: Project identifier

        Returns:
            Workload analysis results
        """
        try:
            # Check cache first
            if self._is_cache_valid(project_id):
                return self._workload_cache[project_id]

            # Get team members
            team_members = await self._get_team_members(project_id)
            if not team_members:
                return WorkloadAnalysis(
                    total_members=0,
                    average_workload=0,
                    workload_distribution={},
                    overloaded_members=[],
                    underutilized_members=[],
                    capacity_utilization={},
                    recommendations=["No team members found"]
                )

            # Get current workloads
            workload_distribution = {}
            capacity_utilization = {}

            for member in team_members.values():
                # Count active tasks for this member
                active_tasks = await self._get_member_active_tasks(member.user_id, project_id)
                workload_distribution[member.user_id] = len(active_tasks)

                # Calculate capacity utilization
                max_capacity = member.availability_hours_per_week / 40  # Normalize to weekly capacity
                utilization = len(active_tasks) / max_capacity if max_capacity > 0 else 0
                capacity_utilization[member.user_id] = min(1.0, utilization)

            # Calculate statistics
            total_members = len(team_members)
            workloads = list(workload_distribution.values())
            average_workload = statistics.mean(workloads) if workloads else 0

            # Identify overloaded and underutilized members
            overloaded_members = []
            underutilized_members = []

            for user_id, utilization in capacity_utilization.items():
                if utilization > 0.8:  # Over 80% capacity
                    overloaded_members.append(user_id)
                elif utilization < 0.3:  # Under 30% capacity
                    underutilized_members.append(user_id)

            # Generate recommendations
            recommendations = self._generate_workload_recommendations(
                workload_distribution, overloaded_members, underutilized_members, average_workload
            )

            analysis = WorkloadAnalysis(
                total_members=total_members,
                average_workload=average_workload,
                workload_distribution=workload_distribution,
                overloaded_members=overloaded_members,
                underutilized_members=underutilized_members,
                capacity_utilization=capacity_utilization,
                recommendations=recommendations,
            )

            # Cache the analysis
            self._workload_cache[project_id] = analysis
            self._cache_expiry[project_id] = datetime.now() + timedelta(minutes=10)

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing workload for project {project_id}: {e}")
            return WorkloadAnalysis(
                total_members=0,
                average_workload=0,
                workload_distribution={},
                overloaded_members=[],
                underutilized_members=[],
                capacity_utilization={},
                recommendations=["Error analyzing workload"]
            )

    async def get_collaboration_metrics(self, project_id: str, days: int = 30) -> CollaborationMetrics:
        """
        Get collaboration metrics for a team.

        Args:
            project_id: Project identifier
            days: Number of days to analyze

        Returns:
            Collaboration metrics
        """
        try:
            # This would analyze various collaboration signals
            # For now, return mock metrics
            return CollaborationMetrics(
                communication_frequency=15.2,  # messages per day
                task_completion_rate=0.85,     # 85% completion rate
                average_response_time=2.3,     # hours
                cross_team_collaboration=0.65, # 65% cross-team interaction
                knowledge_sharing=0.72,        # 72% knowledge sharing score
                conflict_resolution=0.88,      # 88% conflict resolution score
            )

        except Exception as e:
            self.logger.error(f"Error getting collaboration metrics: {e}")
            return CollaborationMetrics(
                communication_frequency=0,
                task_completion_rate=0,
                average_response_time=0,
                cross_team_collaboration=0,
                knowledge_sharing=0,
                conflict_resolution=0,
            )

    async def _apply_assignment_strategy(
        self,
        tasks: List[Dict[str, Any]],
        team_members: Dict[str, TeamMember],
        strategy: TaskAssignmentStrategy
    ) -> Dict[str, str]:
        """Apply the specified assignment strategy."""
        assignments = {}

        if strategy == TaskAssignmentStrategy.WORKLOAD_BALANCE:
            assignments = await self._assign_workload_balance(tasks, team_members)
        elif strategy == TaskAssignmentStrategy.SKILL_BASED:
            assignments = await self._assign_skill_based(tasks, team_members)
        elif strategy == TaskAssignmentStrategy.AVAILABILITY_BASED:
            assignments = await self._assign_availability_based(tasks, team_members)
        elif strategy == TaskAssignmentStrategy.PRIORITY_BASED:
            assignments = await self._assign_priority_based(tasks, team_members)
        else:  # ROUND_ROBIN
            assignments = self._assign_round_robin(tasks, team_members)

        return assignments

    async def _assign_workload_balance(
        self,
        tasks: List[Dict[str, Any]],
        team_members: Dict[str, TeamMember]
    ) -> Dict[str, str]:
        """Assign tasks to balance workload across team members."""
        assignments = {}
        member_workloads = {user_id: member.current_workload for user_id, member in team_members.items()}

        for task in tasks:
            # Find member with lowest workload
            assignee_id = min(member_workloads.keys(), key=lambda x: member_workloads[x])

            assignments[task["id"]] = assignee_id
            member_workloads[assignee_id] += 1

        return assignments

    async def _assign_skill_based(
        self,
        tasks: List[Dict[str, Any]],
        team_members: Dict[str, TeamMember]
    ) -> Dict[str, str]:
        """Assign tasks based on member skills."""
        assignments = {}

        for task in tasks:
            task_skills = set(task.get("required_skills", []))
            best_match = None
            best_score = 0

            for user_id, member in team_members.items():
                # Calculate skill match score
                matching_skills = len(task_skills & member.skills)
                if task_skills:
                    score = matching_skills / len(task_skills)
                else:
                    score = 0.5  # Default score for tasks without specific skills

                if score > best_score:
                    best_score = score
                    best_match = user_id

            if best_match:
                assignments[task["id"]] = best_match

        return assignments

    async def _assign_availability_based(
        self,
        tasks: List[Dict[str, Any]],
        team_members: Dict[str, TeamMember]
    ) -> Dict[str, str]:
        """Assign tasks based on member availability."""
        assignments = {}
        member_utilization = {
            user_id: member.capacity_utilization
            for user_id, member in team_members.items()
        }

        for task in tasks:
            # Find member with lowest utilization
            assignee_id = min(member_utilization.keys(), key=lambda x: member_utilization[x])

            if member_utilization[assignee_id] < 0.9:  # Don't overload over 90%
                assignments[task["id"]] = assignee_id
                # Increase utilization (simplified)
                member_utilization[assignee_id] += 0.1

        return assignments

    async def _assign_priority_based(
        self,
        tasks: List[Dict[str, Any]],
        team_members: Dict[str, TeamMember]
    ) -> Dict[str, str]:
        """Assign high-priority tasks first."""
        # Sort tasks by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_tasks = sorted(
            tasks,
            key=lambda t: priority_order.get(t.get("priority", "medium"), 2)
        )

        # Use workload balancing for assignment
        return await self._assign_workload_balance(sorted_tasks, team_members)

    def _assign_round_robin(
        self,
        tasks: List[Dict[str, Any]],
        team_members: Dict[str, TeamMember]
    ) -> Dict[str, str]:
        """Assign tasks in round-robin fashion."""
        assignments = {}
        member_ids = list(team_members.keys())
        member_index = 0

        for task in tasks:
            assignee_id = member_ids[member_index % len(member_ids)]
            assignments[task["id"]] = assignee_id
            member_index += 1

        return assignments

    def _generate_workload_recommendations(
        self,
        workload_distribution: Dict[str, int],
        overloaded_members: List[str],
        underutilized_members: List[str],
        average_workload: float
    ) -> List[str]:
        """Generate workload balancing recommendations."""
        recommendations = []

        if overloaded_members:
            recommendations.append(
                f"⚠️ {len(overloaded_members)} team members are overloaded. Consider redistributing tasks."
            )

        if underutilized_members:
            recommendations.append(
                f"💡 {len(underutilized_members)} team members have capacity. Consider assigning more tasks."
            )

        # Check workload variance
        workloads = list(workload_distribution.values())
        if workloads and statistics.stdev(workloads) > average_workload * 0.5:
            recommendations.append(
                "📊 Workload distribution is uneven. Consider rebalancing for better team efficiency."
            )

        if not recommendations:
            recommendations.append("✅ Workload distribution is well-balanced.")

        return recommendations

    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        try:
            # This would query user database
            # For now, return mock data
            return {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
            }
        except Exception:
            return None

    async def _get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information."""
        try:
            response = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={"id": task_id}
            )
            tasks = response.get("data", [])
            return tasks[0] if tasks else None
        except Exception:
            return None

    async def _get_team_members(self, project_id: str) -> Dict[str, TeamMember]:
        """Get team members for a project."""
        try:
            # Get team ID for project
            team_response = await self.supabase.select(
                "archon_teams",
                columns=["id"],
                filters={"project_id": project_id}
            )
            teams = team_response.get("data", [])
            if not teams:
                return {}

            team_id = teams[0]["id"]

            # Get team members
            members_response = await self.supabase.select(
                "archon_team_members",
                columns="*",
                filters={"team_id": team_id}
            )

            members = {}
            for m in members_response.get("data", []):
                members[m["user_id"]] = TeamMember(
                    user_id=m["user_id"],
                    username=m["username"],
                    email=m["email"],
                    role=TeamRole(m["role"]),
                    skills=set(m.get("skills", [])),
                    availability_hours_per_week=m.get("availability_hours_per_week", 40),
                    current_workload=m.get("current_workload", 0),
                    capacity_utilization=m.get("capacity_utilization", 0.0),
                    joined_at=datetime.fromisoformat(m["joined_at"].replace('Z', '+00:00')),
                    last_active=datetime.fromisoformat(m["last_active"].replace('Z', '+00:00')),
                )

            return members

        except Exception as e:
            self.logger.error(f"Error getting team members: {e}")
            return {}

    async def _get_team_settings(self, project_id: str) -> Dict[str, Any]:
        """Get team settings for a project."""
        try:
            team_response = await self.supabase.select(
                "archon_teams",
                columns=["settings"],
                filters={"project_id": project_id}
            )
            teams = team_response.get("data", [])
            return teams[0].get("settings", {}) if teams else {}
        except Exception:
            return {}

    async def _get_unassigned_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Get unassigned tasks for a project."""
        try:
            response = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={
                    "project_id": project_id,
                    "assignee": {"$is": None},
                    "status": ["todo", "in_progress"]
                }
            )
            return response.get("data", [])
        except Exception:
            return []

    async def _get_tasks_by_ids(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """Get tasks by their IDs."""
        try:
            response = await self.supabase.select(
                "archon_tasks",
                columns="*",
                filters={"id": task_ids}
            )
            return response.get("data", [])
        except Exception:
            return []

    async def _get_member_active_tasks(self, user_id: str, project_id: str) -> List[Dict[str, Any]]:
        """Get active tasks assigned to a team member."""
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

    async def _validate_assignment(self, task_id: str, assignee_id: str, project_id: str) -> bool:
        """Validate that a task assignment is valid."""
        try:
            # Check if assignee is part of the project team
            team_members = await self._get_team_members(project_id)
            if assignee_id not in team_members:
                return False

            # Check if assignee is overloaded
            member = team_members[assignee_id]
            team_settings = await self._get_team_settings(project_id)
            max_tasks = team_settings.get("max_tasks_per_member", 5)

            if member.current_workload >= max_tasks:
                return False

            return True

        except Exception:
            return False

    async def _notify_assignment(self, assignment: TaskAssignment, project_id: str):
        """Notify team about task assignment."""
        try:
            # This would integrate with the real-time collaboration service
            # For now, just log the assignment
            self.logger.info(f"Task {assignment.task_id} assigned to {assignment.assignee_id}")
        except Exception as e:
            self.logger.warning(f"Error notifying assignment: {e}")

    def _is_cache_valid(self, project_id: str) -> bool:
        """Check if cache entry is still valid."""
        if project_id not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[project_id]

    def _invalidate_cache(self, project_id: str):
        """Invalidate cache for a project."""
        cache_keys = [k for k in self._team_cache.keys() if k == project_id]
        workload_keys = [k for k in self._workload_cache.keys() if k == project_id]
        expiry_keys = [k for k in self._cache_expiry.keys() if k == project_id]

        for key in cache_keys:
            del self._team_cache[key]
        for key in workload_keys:
            del self._workload_cache[key]
        for key in expiry_keys:
            del self._cache_expiry[key]


# Global service instance
team_collaboration_service = TeamCollaborationService()
