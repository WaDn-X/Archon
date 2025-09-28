"""
Smart Suggestions API Endpoints

REST API endpoints for AI-powered task suggestions and recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..services.smart_suggestions_service import smart_suggestions_service
from ..services.auth_service import get_current_user
from ..services.error_service import error_service

router = APIRouter(prefix="/api/smart-suggestions", tags=["Smart Suggestions"])

# Pydantic models for request/response
class SmartSuggestionsRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for suggestions")

class TaskSuggestionResponse(BaseModel):
    task_id: str
    suggestion_type: str
    confidence_score: float
    reasoning: List[str]
    suggested_time: Optional[str]
    estimated_duration: Optional[int]
    prerequisites: List[str]
    expected_impact: str
    alternative_tasks: List[str]

class SmartSuggestionsResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]
    primary_suggestion: Optional[TaskSuggestionResponse]
    alternative_suggestions: List[TaskSuggestionResponse]
    context_analysis: Dict[str, Any]
    user_patterns: Dict[str, Any]
    project_context: Dict[str, Any]
    generated_at: str


@router.post("/suggest", response_model=SmartSuggestionsResponse)
async def get_smart_suggestions(
    request: SmartSuggestionsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get smart task suggestions for a user in a project.

    Uses AI to analyze user patterns, project context, and current situation
    to provide personalized task recommendations.
    """
    try:
        result = await smart_suggestions_service.get_smart_suggestions(
            current_user["user_id"],
            request.project_id,
            request.context
        )

        # Convert to response format
        primary_suggestion = None
        if result.primary_suggestion:
            primary_suggestion = TaskSuggestionResponse(
                task_id=result.primary_suggestion.task_id,
                suggestion_type=result.primary_suggestion.suggestion_type.value,
                confidence_score=result.primary_suggestion.confidence_score,
                reasoning=result.primary_suggestion.reasoning,
                suggested_time=result.primary_suggestion.suggested_time.isoformat() if result.primary_suggestion.suggested_time else None,
                estimated_duration=result.primary_suggestion.estimated_duration,
                prerequisites=result.primary_suggestion.prerequisites,
                expected_impact=result.primary_suggestion.expected_impact,
                alternative_tasks=result.primary_suggestion.alternative_tasks
            )

        alternative_suggestions = []
        for suggestion in result.alternative_suggestions:
            alternative_suggestions.append(TaskSuggestionResponse(
                task_id=suggestion.task_id,
                suggestion_type=suggestion.suggestion_type.value,
                confidence_score=suggestion.confidence_score,
                reasoning=suggestion.reasoning,
                suggested_time=suggestion.suggested_time.isoformat() if suggestion.suggested_time else None,
                estimated_duration=suggestion.estimated_duration,
                prerequisites=suggestion.prerequisites,
                expected_impact=suggestion.expected_impact,
                alternative_tasks=suggestion.alternative_tasks
            ))

        return SmartSuggestionsResponse(
            success=True,
            message="Smart suggestions generated successfully",
            data=result.__dict__,
            primary_suggestion=primary_suggestion,
            alternative_suggestions=alternative_suggestions,
            context_analysis=result.context_analysis,
            user_patterns=result.user_patterns.__dict__,
            project_context=result.project_context,
            generated_at=result.generated_at.isoformat()
        )

    except Exception as e:
        error_service.log_error(
            "SMART_SUGGESTIONS_API_ERROR",
            f"Failed to generate smart suggestions for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to generate smart suggestions")


@router.get("/patterns/{user_id}")
async def get_user_patterns(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user behavior patterns.

    Useful for understanding how suggestions are generated.
    """
    try:
        # Users can only view their own patterns or admins can view any
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        patterns = await smart_suggestions_service._get_user_patterns(user_id)

        return {
            "success": True,
            "message": "User patterns retrieved successfully",
            "data": {
                "user_id": user_id,
                "patterns": patterns.__dict__,
                "last_updated": "recent"  # Could track actual timestamps
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "USER_PATTERNS_API_ERROR",
            f"Failed to get patterns for user {user_id}",
            {"error": str(e), "current_user": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get user patterns")


@router.get("/context/{project_id}")
async def get_project_context(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get project context for suggestions.

    Useful for understanding project-specific factors in suggestions.
    """
    try:
        context = await smart_suggestions_service._get_project_context(project_id, current_user["user_id"])

        return {
            "success": True,
            "message": "Project context retrieved successfully",
            "data": {
                "project_id": project_id,
                "context": context,
                "last_updated": "recent"
            }
        }

    except Exception as e:
        error_service.log_error(
            "PROJECT_CONTEXT_API_ERROR",
            f"Failed to get context for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get project context")


@router.get("/analytics/{project_id}")
async def get_suggestion_analytics(
    project_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get analytics about suggestion effectiveness.

    Shows how well suggestions are performing and user adoption rates.
    """
    try:
        # This would typically query analytics data
        # For now, return mock analytics
        analytics = {
            "suggestion_acceptance_rate": 0.75,
            "average_time_to_action": 45,  # minutes
            "most_helpful_suggestion_types": ["next_best_task", "quick_win", "deadline_driven"],
            "user_engagement_score": 0.82,
            "suggestions_generated": 127,
            "suggestions_accepted": 95,
            "time_period_days": days,
        }

        return {
            "success": True,
            "message": "Suggestion analytics retrieved successfully",
            "data": {
                "project_id": project_id,
                "analytics": analytics,
                "generated_at": "now"
            }
        }

    except Exception as e:
        error_service.log_error(
            "SUGGESTION_ANALYTICS_API_ERROR",
            f"Failed to get analytics for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get suggestion analytics")


@router.post("/feedback/{task_id}")
async def submit_suggestion_feedback(
    task_id: str,
    feedback: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback on a suggestion.

    Helps improve the suggestion algorithm over time.
    """
    try:
        # Validate feedback
        required_fields = ["rating", "usefulness", "suggestion_type"]
        for field in required_fields:
            if field not in feedback:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Store feedback for future analysis
        feedback_data = {
            "task_id": task_id,
            "user_id": current_user["user_id"],
            "feedback": feedback,
            "submitted_at": "now"
        }

        # TODO: Store feedback in database for algorithm improvement

        return {
            "success": True,
            "message": "Suggestion feedback submitted successfully",
            "data": feedback_data
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "SUGGESTION_FEEDBACK_API_ERROR",
            f"Failed to submit feedback for task {task_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/types")
async def get_suggestion_types():
    """
    Get available suggestion types and their descriptions.

    Useful for UI components and documentation.
    """
    try:
        suggestion_types = {
            "next_best_task": {
                "name": "Next Best Task",
                "description": "AI-recommended task based on current context and priorities",
                "icon": "target"
            },
            "high_impact": {
                "name": "High Impact",
                "description": "Tasks that will have significant impact on project progress",
                "icon": "zap"
            },
            "quick_win": {
                "name": "Quick Win",
                "description": "Fast tasks that provide immediate progress feedback",
                "icon": "clock"
            },
            "learning_opportunity": {
                "name": "Learning Opportunity",
                "description": "Tasks that help develop new skills",
                "icon": "book"
            },
            "blocking_task": {
                "name": "Blocking Task",
                "description": "Tasks that are blocking other work",
                "icon": "alert-triangle"
            },
            "deadline_driven": {
                "name": "Deadline Driven",
                "description": "Tasks with approaching deadlines",
                "icon": "calendar"
            },
            "team_collaboration": {
                "name": "Team Collaboration",
                "description": "Tasks that benefit from team input",
                "icon": "users"
            },
            "maintenance_break": {
                "name": "Maintenance Break",
                "description": "Suggested breaks for optimal productivity",
                "icon": "coffee"
            }
        }

        return {
            "success": True,
            "message": "Suggestion types retrieved successfully",
            "data": suggestion_types
        }

    except Exception as e:
        error_service.log_error(
            "SUGGESTION_TYPES_API_ERROR",
            "Failed to get suggestion types",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Failed to get suggestion types")
