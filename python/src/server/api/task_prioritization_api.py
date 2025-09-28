"""
Task Prioritization API Endpoints

REST API endpoints for the intelligent task prioritization service.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..services.task_prioritization_service import task_prioritization_service
from ..services.auth_service import get_current_user
from ..services.error_service import error_service

router = APIRouter(prefix="/api/task-prioritization", tags=["Task Prioritization"])

# Pydantic models for request/response
class PrioritizationRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    user_id: str = Field(..., description="User identifier for pattern analysis")
    task_ids: Optional[List[str]] = Field(None, description="Specific task IDs to prioritize")

class TaskScoreResponse(BaseModel):
    task_id: str
    total_score: float
    priority_level: str
    urgency_level: str
    deadline_score: float
    dependency_score: float
    user_pattern_score: float
    project_context_score: float
    complexity_score: float
    recommended_position: int
    reasoning: List[str]

class PrioritizationResponse(BaseModel):
    success: bool
    message: str
    data: List[TaskScoreResponse]
    total_tasks: int

class FactorUpdateRequest(BaseModel):
    deadline_weight: float = Field(..., ge=0.0, le=1.0)
    dependency_weight: float = Field(..., ge=0.0, le=1.0)
    user_pattern_weight: float = Field(..., ge=0.0, le=1.0)
    project_context_weight: float = Field(..., ge=0.0, le=1.0)
    complexity_weight: float = Field(..., ge=0.0, le=1.0)


@router.post("/prioritize", response_model=PrioritizationResponse)
async def prioritize_tasks(
    request: PrioritizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Prioritize tasks using AI-powered scoring.

    Returns prioritized task list with scores and reasoning.
    """
    try:
        # Prioritize tasks
        task_scores = await task_prioritization_service.prioritize_tasks(
            request.project_id,
            request.user_id or current_user["user_id"],
            request.task_ids
        )

        # Convert to response format
        response_data = []
        for score in task_scores:
            response_data.append(TaskScoreResponse(
                task_id=score.task_id,
                total_score=score.total_score,
                priority_level=score.priority_level.value,
                urgency_level=score.urgency_level.value,
                deadline_score=score.deadline_score,
                dependency_score=score.dependency_score,
                user_pattern_score=score.user_pattern_score,
                project_context_score=score.project_context_score,
                complexity_score=score.complexity_score,
                recommended_position=score.recommended_position,
                reasoning=score.reasoning
            ))

        return PrioritizationResponse(
            success=True,
            message="Tasks prioritized successfully",
            data=response_data,
            total_tasks=len(response_data)
        )

    except Exception as e:
        error_service.log_error(
            "TASK_PRIORITIZATION_API_ERROR",
            f"Failed to prioritize tasks for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to prioritize tasks")


@router.get("/recommendations/{project_id}")
async def get_task_recommendations(
    project_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get personalized task recommendations for a user.

    Returns top recommended tasks with reasoning.
    """
    try:
        recommendations = await task_prioritization_service.get_task_recommendations(
            current_user["user_id"],
            project_id,
            limit
        )

        return {
            "success": True,
            "message": "Task recommendations retrieved successfully",
            "data": recommendations,
            "total_recommendations": len(recommendations)
        }

    except Exception as e:
        error_service.log_error(
            "TASK_RECOMMENDATIONS_API_ERROR",
            f"Failed to get recommendations for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get task recommendations")


@router.put("/factors")
async def update_prioritization_factors(
    request: FactorUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update task prioritization factors.

    Only administrators should be able to modify these.
    """
    try:
        # TODO: Add admin permission check
        # if not current_user.get("role") == "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")

        success = await task_prioritization_service.update_factors(request.dict())

        if not success:
            raise HTTPException(status_code=400, detail="Invalid factor weights - must sum to 1.0")

        return {
            "success": True,
            "message": "Prioritization factors updated successfully",
            "data": request.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "UPDATE_FACTORS_API_ERROR",
            "Failed to update prioritization factors",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to update factors")


@router.get("/factors")
async def get_prioritization_factors(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current task prioritization factors.
    """
    try:
        factors = task_prioritization_service.factors

        return {
            "success": True,
            "message": "Prioritization factors retrieved successfully",
            "data": {
                "deadline_weight": factors.deadline_weight,
                "dependency_weight": factors.dependency_weight,
                "user_pattern_weight": factors.user_pattern_weight,
                "project_context_weight": factors.project_context_weight,
                "complexity_weight": factors.complexity_weight
            }
        }

    except Exception as e:
        error_service.log_error(
            "GET_FACTORS_API_ERROR",
            "Failed to retrieve prioritization factors",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve factors")


@router.delete("/cache/{project_id}")
async def invalidate_project_cache(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Invalidate cache for a specific project.

    Useful when project data has been significantly updated.
    """
    try:
        task_prioritization_service.invalidate_cache(project_id)

        return {
            "success": True,
            "message": f"Cache invalidated for project {project_id}"
        }

    except Exception as e:
        error_service.log_error(
            "INVALIDATE_CACHE_API_ERROR",
            f"Failed to invalidate cache for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")
