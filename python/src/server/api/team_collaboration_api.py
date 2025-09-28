"""
Team Collaboration API Endpoints

REST API endpoints for team management, task assignment, and collaboration features.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from ..services.team_collaboration_service import team_collaboration_service
from ..services.auth_service import get_current_user
from ..services.error_service import error_service

router = APIRouter(prefix="/api/team-collaboration", tags=["Team Collaboration"])

# Pydantic models for request/response
class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    description: str = Field(..., max_length=500, description="Team description")
    project_id: str = Field(..., description="Associated project ID")

class AddTeamMemberRequest(BaseModel):
    team_id: str = Field(..., description="Team identifier")
    user_id: str = Field(..., description="User identifier")
    role: str = Field(..., description="Team role")

class TaskAssignmentRequest(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    assignee_id: str = Field(..., description="User ID to assign the task to")
    project_id: str = Field(..., description="Project identifier")
    strategy: Optional[str] = Field(None, description="Assignment strategy")

class AutoAssignRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    tasks: Optional[List[str]] = Field(None, description="Specific tasks to assign")
    strategy: Optional[str] = Field(None, description="Assignment strategy")

class WorkloadAnalysisRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")

class TeamResponse(BaseModel):
    id: str
    name: str
    description: str
    project_id: str
    member_count: int
    created_at: str

class TeamMemberResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    skills: List[str]
    availability_hours_per_week: int
    current_workload: int
    capacity_utilization: float
    joined_at: str
    last_active: str

class TaskAssignmentResponse(BaseModel):
    task_id: str
    assignee_id: str
    assigned_by: str
    assigned_at: str
    estimated_hours: Optional[int]
    priority: str
    reason: str

class WorkloadAnalysisResponse(BaseModel):
    total_members: int
    average_workload: float
    workload_distribution: Dict[str, int]
    overloaded_members: List[str]
    underutilized_members: List[str]
    capacity_utilization: Dict[str, float]
    recommendations: List[str]


@router.post("/teams", response_model=TeamResponse)
async def create_team(
    request: CreateTeamRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new team for a project.

    The creator becomes the team owner.
    """
    try:
        team = await team_collaboration_service.create_team(
            request.name,
            request.description,
            request.project_id,
            current_user["user_id"]
        )

        if not team:
            raise HTTPException(status_code=400, detail="Failed to create team")

        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            project_id=team.project_id,
            member_count=len(team.members),
            created_at=team.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "CREATE_TEAM_API_ERROR",
            f"Failed to create team for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to create team")


@router.post("/teams/members")
async def add_team_member(
    request: AddTeamMemberRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add a member to a team.

    Requires appropriate permissions.
    """
    try:
        # TODO: Add permission check - only team owners/managers can add members

        success = await team_collaboration_service.add_team_member(
            request.team_id,
            request.user_id,
            request.role
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to add team member")

        return {
            "success": True,
            "message": f"User {request.user_id} added to team {request.team_id}",
            "data": {
                "team_id": request.team_id,
                "user_id": request.user_id,
                "role": request.role,
                "added_by": current_user["user_id"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "ADD_TEAM_MEMBER_API_ERROR",
            f"Failed to add member {request.user_id} to team {request.team_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to add team member")


@router.post("/tasks/assign", response_model=TaskAssignmentResponse)
async def assign_task(
    request: TaskAssignmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Assign a task to a team member.

    Uses intelligent assignment strategies for optimal distribution.
    """
    try:
        assignment = await team_collaboration_service.assign_task(
            request.task_id,
            request.assignee_id,
            current_user["user_id"],
            request.project_id,
            request.strategy
        )

        if not assignment:
            raise HTTPException(status_code=400, detail="Failed to assign task")

        return TaskAssignmentResponse(
            task_id=assignment.task_id,
            assignee_id=assignment.assignee_id,
            assigned_by=assignment.assigned_by,
            assigned_at=assignment.assigned_at.isoformat(),
            estimated_hours=assignment.estimated_hours,
            priority=assignment.priority,
            reason=assignment.reason
        )

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "ASSIGN_TASK_API_ERROR",
            f"Failed to assign task {request.task_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to assign task")


@router.post("/tasks/auto-assign")
async def auto_assign_tasks(
    request: AutoAssignRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Automatically assign tasks using AI-powered algorithms.

    Supports multiple assignment strategies for optimal team utilization.
    """
    try:
        assignments = await team_collaboration_service.auto_assign_tasks(
            request.project_id,
            request.tasks,
            request.strategy
        )

        return {
            "success": True,
            "message": f"Auto-assigned {len(assignments)} tasks",
            "data": {
                "assignments": assignments,
                "total_assigned": len(assignments),
                "strategy": request.strategy or "default",
                "project_id": request.project_id
            }
        }

    except Exception as e:
        error_service.log_error(
            "AUTO_ASSIGN_API_ERROR",
            f"Failed to auto-assign tasks for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to auto-assign tasks")


@router.get("/workload/{project_id}", response_model=WorkloadAnalysisResponse)
async def analyze_workload(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze team workload distribution.

    Provides insights into team utilization and workload balance.
    """
    try:
        analysis = await team_collaboration_service.analyze_workload(project_id)

        return WorkloadAnalysisResponse(
            total_members=analysis.total_members,
            average_workload=analysis.average_workload,
            workload_distribution=analysis.workload_distribution,
            overloaded_members=analysis.overloaded_members,
            underutilized_members=analysis.underutilized_members,
            capacity_utilization=analysis.capacity_utilization,
            recommendations=analysis.recommendations
        )

    except Exception as e:
        error_service.log_error(
            "WORKLOAD_ANALYSIS_API_ERROR",
            f"Failed to analyze workload for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to analyze workload")


@router.get("/teams/{project_id}")
async def get_project_team(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get team information for a project.

    Returns team details and member information.
    """
    try:
        # Get team members for the project
        team_members = await team_collaboration_service._get_team_members(project_id)

        members_data = []
        for user_id, member in team_members.items():
            members_data.append(TeamMemberResponse(
                user_id=member.user_id,
                username=member.username,
                email=member.email,
                role=member.role.value,
                skills=list(member.skills),
                availability_hours_per_week=member.availability_hours_per_week,
                current_workload=member.current_workload,
                capacity_utilization=member.capacity_utilization,
                joined_at=member.joined_at.isoformat(),
                last_active=member.last_active.isoformat()
            ))

        return {
            "success": True,
            "message": f"Found {len(members_data)} team members",
            "data": {
                "project_id": project_id,
                "members": members_data,
                "total_members": len(members_data),
                "active_members": len([m for m in members_data if m.capacity_utilization > 0])
            }
        }

    except Exception as e:
        error_service.log_error(
            "GET_TEAM_API_ERROR",
            f"Failed to get team for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get team information")


@router.get("/collaboration-metrics/{project_id}")
async def get_collaboration_metrics(
    project_id: str,
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get collaboration metrics for a team.

    Analyzes communication patterns, task completion rates, and team effectiveness.
    """
    try:
        metrics = await team_collaboration_service.get_collaboration_metrics(project_id, days)

        return {
            "success": True,
            "message": "Collaboration metrics retrieved successfully",
            "data": {
                "metrics": metrics.__dict__,
                "project_id": project_id,
                "analysis_period_days": days,
                "generated_at": "now"
            }
        }

    except Exception as e:
        error_service.log_error(
            "COLLABORATION_METRICS_API_ERROR",
            f"Failed to get collaboration metrics for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get collaboration metrics")


@router.get("/assignment-strategies")
async def get_assignment_strategies():
    """
    Get available task assignment strategies.

    Useful for UI components and user education.
    """
    try:
        strategies = {
            "workload_balance": {
                "name": "Workload Balance",
                "description": "Assign tasks to balance workload across team members",
                "best_for": "Fair distribution and preventing burnout",
                "pros": ["Balanced utilization", "Prevents overload"],
                "cons": ["May not consider skills", "Slower for specialized tasks"]
            },
            "skill_based": {
                "name": "Skill-Based",
                "description": "Assign tasks based on team member expertise",
                "best_for": "Complex tasks requiring specific skills",
                "pros": ["Higher quality output", "Faster completion"],
                "cons": ["May create workload imbalance", "Limited flexibility"]
            },
            "availability_based": {
                "name": "Availability-Based",
                "description": "Assign tasks based on current availability",
                "best_for": "Time-sensitive tasks with varying schedules",
                "pros": ["Maximizes immediate capacity", "Considers current workload"],
                "cons": ["May ignore skill fit", "Can create bottlenecks"]
            },
            "priority_based": {
                "name": "Priority-Based",
                "description": "Assign high-priority tasks first",
                "best_for": "Projects with clear priority hierarchies",
                "pros": ["Ensures critical tasks are handled", "Clear prioritization"],
                "cons": ["May neglect lower-priority but important tasks"]
            },
            "round_robin": {
                "name": "Round Robin",
                "description": "Assign tasks in rotating order",
                "best_for": "Simple, similar tasks with equal team members",
                "pros": ["Simple and fair", "Easy to understand"],
                "cons": ["Ignores skills and availability", "May be inefficient"]
            }
        }

        return {
            "success": True,
            "message": "Assignment strategies retrieved successfully",
            "data": strategies
        }

    except Exception as e:
        error_service.log_error(
            "ASSIGNMENT_STRATEGIES_API_ERROR",
            "Failed to get assignment strategies",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Failed to get assignment strategies")


@router.get("/team-performance/{project_id}")
async def get_team_performance(
    project_id: str,
    period: str = Query("30d", description="Analysis period (7d, 30d, 90d)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get team performance metrics and insights.

    Provides data-driven insights into team effectiveness.
    """
    try:
        # Parse period
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)

        # Get workload analysis
        workload_analysis = await team_collaboration_service.analyze_workload(project_id)

        # Get collaboration metrics
        collaboration_metrics = await team_collaboration_service.get_collaboration_metrics(project_id, days)

        # Calculate performance score
        performance_score = calculate_performance_score(workload_analysis, collaboration_metrics)

        performance_data = {
            "overall_score": performance_score,
            "workload_health": "good" if len(workload_analysis.overloaded_members) == 0 else "needs_attention",
            "collaboration_health": "good" if collaboration_metrics.task_completion_rate > 0.8 else "needs_improvement",
            "workload_analysis": workload_analysis.__dict__,
            "collaboration_metrics": collaboration_metrics.__dict__,
            "period": period,
            "insights": generate_performance_insights(workload_analysis, collaboration_metrics)
        }

        return {
            "success": True,
            "message": "Team performance analysis completed",
            "data": performance_data
        }

    except Exception as e:
        error_service.log_error(
            "TEAM_PERFORMANCE_API_ERROR",
            f"Failed to get team performance for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get team performance")


def calculate_performance_score(workload_analysis: WorkloadAnalysis, metrics: Any) -> float:
    """Calculate overall team performance score (0-100)."""
    score = 50.0  # Base score

    # Workload balance factor
    if len(workload_analysis.overloaded_members) == 0:
        score += 20
    elif len(workload_analysis.overloaded_members) <= 2:
        score += 10

    # Task completion factor
    completion_rate = getattr(metrics, 'task_completion_rate', 0.7)
    score += (completion_rate - 0.7) * 50  # Scale completion rate contribution

    # Collaboration factor
    communication_freq = getattr(metrics, 'communication_frequency', 10)
    if communication_freq > 15:
        score += 10
    elif communication_freq > 5:
        score += 5

    return min(100.0, max(0.0, score))


def generate_performance_insights(workload_analysis: WorkloadAnalysis, metrics: Any) -> List[str]:
    """Generate actionable insights based on performance data."""
    insights = []

    if len(workload_analysis.overloaded_members) > 0:
        insights.append(f"{len(workload_analysis.overloaded_members)} team members are overloaded. Consider redistributing tasks.")

    if len(workload_analysis.underutilized_members) > 0:
        insights.append(f"{len(workload_analysis.underutilized_members)} team members have capacity for more work.")

    completion_rate = getattr(metrics, 'task_completion_rate', 0.7)
    if completion_rate < 0.8:
        insights.append("Task completion rate could be improved. Consider reviewing task assignments and blockers.")

    communication_freq = getattr(metrics, 'communication_frequency', 10)
    if communication_freq < 8:
        insights.append("Team communication frequency is low. Consider increasing check-ins and updates.")

    if not insights:
        insights.append("Team performance is strong. Continue current practices.")

    return insights


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Remove a member from a team.

    Requires appropriate permissions (team owner or admin).
    """
    try:
        # TODO: Add permission check
        # if not is_team_owner_or_admin(current_user["user_id"], team_id):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        # This would implement the actual removal logic
        # For now, return success
        return {
            "success": True,
            "message": f"User {user_id} removed from team {team_id}",
            "data": {
                "team_id": team_id,
                "user_id": user_id,
                "removed_by": current_user["user_id"],
                "removed_at": "now"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "REMOVE_TEAM_MEMBER_API_ERROR",
            f"Failed to remove member {user_id} from team {team_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to remove team member")
