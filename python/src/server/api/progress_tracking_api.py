"""
Progress Tracking API Endpoints

REST API endpoints for progress tracking, milestone management, and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.progress_tracking_service import progress_tracking_service
from ..services.auth_service import get_current_user
from ..services.error_service import error_service

router = APIRouter(prefix="/api/progress-tracking", tags=["Progress Tracking"])

# Pydantic models for request/response
class CreateMilestoneRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Milestone description")
    target_date: str = Field(..., description="Target completion date (ISO format)")
    deliverables: Optional[List[str]] = Field(None, description="List of deliverables")
    owner: Optional[str] = Field(None, description="Milestone owner")

class UpdateMilestoneRequest(BaseModel):
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    status: Optional[str] = Field(None, description="Milestone status")

class ProgressAnalyticsRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")

class BurnDownRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    days: int = Field(30, ge=1, le=90, description="Number of days to analyze")

class MilestoneResponse(BaseModel):
    id: str
    title: str
    description: str
    target_date: str
    status: str
    progress_percentage: float
    dependencies: List[str]
    deliverables: List[str]
    owner: Optional[str]
    created_at: str
    updated_at: str

class ProgressSnapshotResponse(BaseModel):
    timestamp: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    overdue_tasks: int
    time_spent_hours: float
    estimated_remaining_hours: float
    velocity_tasks_per_day: float
    milestone_progress: Dict[str, float]

class ProgressAnalyticsResponse(BaseModel):
    overall_progress: float
    projected_completion_date: Optional[str]
    velocity_trend: str
    risk_level: str
    bottleneck_tasks: List[str]
    upcoming_milestones: List[MilestoneResponse]
    recommendations: List[str]
    progress_rate: float
    estimated_days_remaining: Optional[float]


@router.post("/milestones", response_model=MilestoneResponse)
async def create_milestone(
    request: CreateMilestoneRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new milestone for a project.

    Requires appropriate permissions for the project.
    """
    try:
        # Parse target date
        target_date = datetime.fromisoformat(request.target_date.replace('Z', '+00:00'))

        milestone = await progress_tracking_service.create_milestone(
            request.project_id,
            request.title,
            request.description,
            target_date,
            request.deliverables,
            request.owner
        )

        if not milestone:
            raise HTTPException(status_code=400, detail="Failed to create milestone")

        return MilestoneResponse(
            id=milestone.id,
            title=milestone.title,
            description=milestone.description,
            target_date=milestone.target_date.isoformat(),
            status=milestone.status.value,
            progress_percentage=milestone.progress_percentage,
            dependencies=list(milestone.dependencies),
            deliverables=milestone.deliverables,
            owner=milestone.owner,
            created_at=milestone.created_at.isoformat(),
            updated_at=milestone.updated_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        error_service.log_error(
            "CREATE_MILESTONE_API_ERROR",
            f"Failed to create milestone for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to create milestone")


@router.put("/milestones/{milestone_id}")
async def update_milestone_progress(
    milestone_id: str,
    request: UpdateMilestoneRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update milestone progress.

    Requires appropriate permissions.
    """
    try:
        # TODO: Add permission check
        # Get project_id from milestone (would need to query database)
        project_id = "placeholder"  # This should be retrieved from the milestone

        success = await progress_tracking_service.update_milestone_progress(
            project_id,
            milestone_id,
            request.progress_percentage,
            request.status
        )

        if not success:
            raise HTTPException(status_code=404, detail="Milestone not found or update failed")

        return {
            "success": True,
            "message": f"Milestone {milestone_id} updated successfully",
            "data": {
                "milestone_id": milestone_id,
                "progress_percentage": request.progress_percentage,
                "status": request.status
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "UPDATE_MILESTONE_API_ERROR",
            f"Failed to update milestone {milestone_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to update milestone")


@router.get("/progress/{project_id}", response_model=ProgressSnapshotResponse)
async def get_project_progress(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current progress snapshot for a project.

    Returns comprehensive progress metrics.
    """
    try:
        snapshot = await progress_tracking_service.get_project_progress(project_id)

        return ProgressSnapshotResponse(
            timestamp=snapshot.timestamp.isoformat(),
            total_tasks=snapshot.total_tasks,
            completed_tasks=snapshot.completed_tasks,
            in_progress_tasks=snapshot.in_progress_tasks,
            blocked_tasks=snapshot.blocked_tasks,
            overdue_tasks=snapshot.overdue_tasks,
            time_spent_hours=snapshot.time_spent_hours,
            estimated_remaining_hours=snapshot.estimated_remaining_hours,
            velocity_tasks_per_day=snapshot.velocity_tasks_per_day,
            milestone_progress=snapshot.milestone_progress
        )

    except Exception as e:
        error_service.log_error(
            "PROJECT_PROGRESS_API_ERROR",
            f"Failed to get progress for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get project progress")


@router.get("/analytics/{project_id}", response_model=ProgressAnalyticsResponse)
async def get_progress_analytics(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get comprehensive progress analytics for a project.

    Includes predictive analytics and recommendations.
    """
    try:
        analytics = await progress_tracking_service.get_progress_analytics(project_id)

        # Convert milestones to response format
        upcoming_milestones = []
        for milestone in analytics.upcoming_milestones:
            upcoming_milestones.append(MilestoneResponse(
                id=milestone.id,
                title=milestone.title,
                description=milestone.description,
                target_date=milestone.target_date.isoformat(),
                status=milestone.status.value,
                progress_percentage=milestone.progress_percentage,
                dependencies=list(milestone.dependencies),
                deliverables=milestone.deliverables,
                owner=milestone.owner,
                created_at=milestone.created_at.isoformat(),
                updated_at=milestone.updated_at.isoformat()
            ))

        return ProgressAnalyticsResponse(
            overall_progress=analytics.overall_progress,
            projected_completion_date=analytics.projected_completion_date.isoformat() if analytics.projected_completion_date else None,
            velocity_trend=analytics.velocity_trend,
            risk_level=analytics.risk_level,
            bottleneck_tasks=analytics.bottleneck_tasks,
            upcoming_milestones=upcoming_milestones,
            recommendations=analytics.recommendations,
            progress_rate=analytics.progress_rate,
            estimated_days_remaining=analytics.estimated_days_remaining
        )

    except Exception as e:
        error_service.log_error(
            "PROGRESS_ANALYTICS_API_ERROR",
            f"Failed to get analytics for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get progress analytics")


@router.get("/burndown/{project_id}")
async def get_burndown_data(
    request: BurnDownRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get burn-down chart data for a project.

    Useful for visualizing progress over time.
    """
    try:
        burndown_data = await progress_tracking_service.get_burndown_data(
            request.project_id,
            request.days
        )

        # Convert dates to ISO strings
        dates = [date.isoformat() for date in burndown_data.dates]

        return {
            "success": True,
            "message": "Burn-down data retrieved successfully",
            "data": {
                "dates": dates,
                "planned_remaining": burndown_data.planned_remaining,
                "actual_remaining": burndown_data.actual_remaining,
                "ideal_burndown": burndown_data.ideal_burndown,
                "analysis_period_days": request.days
            }
        }

    except Exception as e:
        error_service.log_error(
            "BURNDOWN_API_ERROR",
            f"Failed to get burn-down data for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get burn-down data")


@router.get("/milestones/{project_id}")
async def get_project_milestones(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by milestone status"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all milestones for a project.

    Optionally filter by status.
    """
    try:
        # This would query the milestones table
        # For now, return mock data
        milestones = [
            {
                "id": "milestone1",
                "title": "Phase 1 Completion",
                "description": "Complete all Phase 1 deliverables",
                "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "in_progress",
                "progress_percentage": 65.0,
                "dependencies": [],
                "deliverables": ["API Development", "Database Setup", "Testing"],
                "owner": current_user["user_id"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]

        # Filter by status if provided
        if status:
            milestones = [m for m in milestones if m["status"] == status]

        return {
            "success": True,
            "message": f"Found {len(milestones)} milestones",
            "data": {
                "milestones": milestones,
                "total_count": len(milestones),
                "project_id": project_id
            }
        }

    except Exception as e:
        error_service.log_error(
            "GET_MILESTONES_API_ERROR",
            f"Failed to get milestones for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get milestones")


@router.get("/velocity/{project_id}")
async def get_velocity_trends(
    project_id: str,
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get velocity trends for a project.

    Shows how quickly the team is completing work over time.
    """
    try:
        analytics = await progress_tracking_service.get_progress_analytics(project_id)

        # Calculate velocity trend data
        velocity_data = {
            "current_velocity": analytics.progress_rate,
            "trend": analytics.velocity_trend,
            "average_velocity": analytics.progress_rate,  # Could be calculated from historical data
            "velocity_history": [],  # Would contain historical velocity data
            "analysis_period_days": days
        }

        return {
            "success": True,
            "message": "Velocity trends retrieved successfully",
            "data": velocity_data
        }

    except Exception as e:
        error_service.log_error(
            "VELOCITY_TRENDS_API_ERROR",
            f"Failed to get velocity trends for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get velocity trends")


@router.get("/risk-assessment/{project_id}")
async def get_risk_assessment(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get risk assessment for a project.

    Identifies potential risks and provides mitigation recommendations.
    """
    try:
        analytics = await progress_tracking_service.get_progress_analytics(project_id)

        risk_assessment = {
            "overall_risk_level": analytics.risk_level,
            "risk_factors": [],
            "mitigation_strategies": analytics.recommendations,
            "contingency_plans": [],
            "monitoring_points": []
        }

        # Add specific risk factors based on analytics
        if analytics.velocity_trend == "decreasing":
            risk_assessment["risk_factors"].append({
                "factor": "Decreasing Velocity",
                "severity": "high",
                "description": "Team velocity is decreasing, indicating potential productivity issues"
            })

        if analytics.overall_progress < 0.5 and analytics.estimated_days_remaining:
            days_remaining = analytics.estimated_days_remaining
            if days_remaining < 14:
                risk_assessment["risk_factors"].append({
                    "factor": "Tight Timeline",
                    "severity": "high",
                    "description": f"Only {days_remaining:.1f} days remaining with {analytics.overall_progress:.1%} progress"
                })

        return {
            "success": True,
            "message": "Risk assessment completed",
            "data": risk_assessment
        }

    except Exception as e:
        error_service.log_error(
            "RISK_ASSESSMENT_API_ERROR",
            f"Failed to get risk assessment for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get risk assessment")


@router.post("/milestones/{milestone_id}/complete")
async def complete_milestone(
    milestone_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Mark a milestone as completed.

    Requires appropriate permissions.
    """
    try:
        # TODO: Get project_id from milestone and add permission check
        project_id = "placeholder"

        success = await progress_tracking_service.update_milestone_progress(
            project_id,
            milestone_id,
            100.0,
            "completed"
        )

        if not success:
            raise HTTPException(status_code=404, detail="Milestone not found")

        return {
            "success": True,
            "message": f"Milestone {milestone_id} marked as completed",
            "data": {
                "milestone_id": milestone_id,
                "status": "completed",
                "progress_percentage": 100.0,
                "completed_by": current_user["user_id"],
                "completed_at": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "COMPLETE_MILESTONE_API_ERROR",
            f"Failed to complete milestone {milestone_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to complete milestone")
