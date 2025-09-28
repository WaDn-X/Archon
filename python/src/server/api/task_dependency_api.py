"""
Task Dependency API Endpoints

REST API endpoints for task dependency mapping and critical path analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..services.task_dependency_service import task_dependency_service
from ..services.auth_service import get_current_user
from ..services.error_service import error_service

router = APIRouter(prefix="/api/task-dependencies", tags=["Task Dependencies"])

# Pydantic models for request/response
class DependencyGraphRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")

class CriticalPathRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")

class ImpactAnalysisRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    task_id: str = Field(..., description="Task identifier")
    change_type: str = Field(..., description="Type of change (delay, deletion, etc.)")

class TaskDependencyResponse(BaseModel):
    from_task: str
    to_task: str
    dependency_type: str
    strength: str
    lag_time: int
    created_at: str

class CriticalPathResponse(BaseModel):
    critical_path: List[str]
    total_duration: int
    slack_times: Dict[str, int]
    earliest_start: Dict[str, str]
    latest_start: Dict[str, str]
    earliest_finish: Dict[str, str]
    latest_finish: Dict[str, str]

class ImpactAnalysisResponse(BaseModel):
    task_id: str
    change_type: str
    affected_tasks: Dict[str, List[str]]
    impact_metrics: Dict[str, Any]
    recommendations: List[str]


@router.get("/graph/{project_id}")
async def get_dependency_graph(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the complete dependency graph for a project.

    Returns nodes (tasks) and edges (dependencies) for visualization.
    """
    try:
        visualization_data = await task_dependency_service.get_dependency_visualization_data(project_id)

        return {
            "success": True,
            "message": "Dependency graph retrieved successfully",
            "data": visualization_data
        }

    except Exception as e:
        error_service.log_error(
            "DEPENDENCY_GRAPH_API_ERROR",
            f"Failed to get dependency graph for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get dependency graph")


@router.get("/critical-path/{project_id}", response_model=CriticalPathResponse)
async def get_critical_path(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Calculate and return the critical path for a project.

    The critical path shows the sequence of tasks that determine project duration.
    """
    try:
        critical_path_result = await task_dependency_service.calculate_critical_path(project_id)

        if not critical_path_result:
            return CriticalPathResponse(
                critical_path=[],
                total_duration=0,
                slack_times={},
                earliest_start={},
                latest_start={},
                earliest_finish={},
                latest_finish={}
            )

        # Convert datetime objects to ISO strings
        earliest_start = {k: v.isoformat() for k, v in critical_path_result.earliest_start.items()}
        latest_start = {k: v.isoformat() for k, v in critical_path_result.latest_start.items()}
        earliest_finish = {k: v.isoformat() for k, v in critical_path_result.earliest_finish.items()}
        latest_finish = {k: v.isoformat() for k, v in critical_path_result.latest_finish.items()}

        return CriticalPathResponse(
            critical_path=critical_path_result.critical_path,
            total_duration=critical_path_result.total_duration,
            slack_times=critical_path_result.slack_times,
            earliest_start=earliest_start,
            latest_start=latest_start,
            earliest_finish=earliest_finish,
            latest_finish=latest_finish
        )

    except Exception as e:
        error_service.log_error(
            "CRITICAL_PATH_API_ERROR",
            f"Failed to calculate critical path for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to calculate critical path")


@router.post("/impact-analysis", response_model=ImpactAnalysisResponse)
async def analyze_task_impact(
    request: ImpactAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze the impact of a change to a task on the entire project.

    Helps understand the ripple effects of task modifications.
    """
    try:
        impact_analysis = await task_dependency_service.analyze_impact(
            request.project_id,
            request.task_id,
            request.change_type
        )

        return ImpactAnalysisResponse(**impact_analysis)

    except Exception as e:
        error_service.log_error(
            "IMPACT_ANALYSIS_API_ERROR",
            f"Failed to analyze impact for task {request.task_id}",
            {"error": str(e), "user_id": current_user["user_id"], "project_id": request.project_id}
        )
        raise HTTPException(status_code=500, detail="Failed to analyze task impact")


@router.get("/slack-times/{project_id}")
async def get_slack_times(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get slack times for all tasks in a project.

    Slack time shows how much flexibility exists in task scheduling.
    """
    try:
        critical_path_result = await task_dependency_service.calculate_critical_path(project_id)

        if not critical_path_result:
            return {
                "success": True,
                "message": "No slack time data available",
                "data": {"slack_times": {}}
            }

        return {
            "success": True,
            "message": "Slack times retrieved successfully",
            "data": {
                "slack_times": critical_path_result.slack_times,
                "critical_path": critical_path_result.critical_path,
                "total_duration": critical_path_result.total_duration
            }
        }

    except Exception as e:
        error_service.log_error(
            "SLACK_TIMES_API_ERROR",
            f"Failed to get slack times for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get slack times")


@router.get("/bottlenecks/{project_id}")
async def identify_bottlenecks(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Identify bottleneck tasks in a project.

    Bottlenecks are tasks that are causing delays or blocking progress.
    """
    try:
        graph = await task_dependency_service.build_dependency_graph(project_id)

        # Simple bottleneck detection based on dependencies
        bottlenecks = []
        for node_id, node in graph.nodes.items():
            dependency_count = len(node.predecessors) + len(node.successors)
            if dependency_count >= 3:  # Tasks with many dependencies
                bottlenecks.append({
                    "task_id": node_id,
                    "task_title": node.title,
                    "dependency_count": dependency_count,
                    "status": node.status,
                    "bottleneck_type": "high_dependency"
                })

        # Add tasks with long estimated duration
        for node_id, node in graph.nodes.items():
            if node.estimated_duration and node.estimated_duration >= 480:  # 8+ hours
                if not any(b["task_id"] == node_id for b in bottlenecks):
                    bottlenecks.append({
                        "task_id": node_id,
                        "task_title": node.title,
                        "estimated_duration": node.estimated_duration,
                        "status": node.status,
                        "bottleneck_type": "long_duration"
                    })

        return {
            "success": True,
            "message": f"Found {len(bottlenecks)} potential bottlenecks",
            "data": {
                "bottlenecks": bottlenecks,
                "total_analyzed": len(graph.nodes),
                "analysis_timestamp": graph.last_updated.isoformat()
            }
        }

    except Exception as e:
        error_service.log_error(
            "BOTTLENECKS_API_ERROR",
            f"Failed to identify bottlenecks for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to identify bottlenecks")


@router.get("/dependencies/{project_id}")
async def get_project_dependencies(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all dependencies for a project.

    Returns explicit and implicit dependencies between tasks.
    """
    try:
        graph = await task_dependency_service.build_dependency_graph(project_id)

        dependencies = []
        for edge in graph.edges:
            dependencies.append({
                "from_task": edge.from_task,
                "to_task": edge.to_task,
                "dependency_type": edge.dependency_type.value,
                "strength": edge.strength.value,
                "lag_time": edge.lag_time,
                "created_at": edge.created_at.isoformat()
            })

        return {
            "success": True,
            "message": f"Found {len(dependencies)} dependencies",
            "data": {
                "dependencies": dependencies,
                "has_cycles": len(graph.cycles) > 0,
                "cycles": graph.cycles,
                "total_tasks": len(graph.nodes)
            }
        }

    except Exception as e:
        error_service.log_error(
            "DEPENDENCIES_API_ERROR",
            f"Failed to get dependencies for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get dependencies")


@router.delete("/cache/{project_id}")
async def invalidate_dependency_cache(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Invalidate dependency cache for a project.

    Useful when project structure has changed significantly.
    """
    try:
        task_dependency_service.invalidate_cache(project_id)

        return {
            "success": True,
            "message": f"Dependency cache invalidated for project {project_id}"
        }

    except Exception as e:
        error_service.log_error(
            "INVALIDATE_DEPENDENCY_CACHE_API_ERROR",
            f"Failed to invalidate dependency cache for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.get("/health/{project_id}")
async def get_dependency_health(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get health status of dependency analysis for a project.

    Useful for monitoring and debugging.
    """
    try:
        graph = await task_dependency_service.build_dependency_graph(project_id)

        health_data = {
            "total_tasks": len(graph.nodes),
            "total_dependencies": len(graph.edges),
            "has_cycles": len(graph.cycles) > 0,
            "cycle_count": len(graph.cycles),
            "last_updated": graph.last_updated.isoformat(),
            "cache_status": "fresh"
        }

        # Determine health status
        if health_data["has_cycles"]:
            health_data["status"] = "warning"
            health_data["issues"] = ["Circular dependencies detected"]
        elif health_data["total_tasks"] == 0:
            health_data["status"] = "info"
            health_data["issues"] = ["No tasks found"]
        else:
            health_data["status"] = "healthy"
            health_data["issues"] = []

        return {
            "success": True,
            "message": "Dependency health check completed",
            "data": health_data
        }

    except Exception as e:
        error_service.log_error(
            "DEPENDENCY_HEALTH_API_ERROR",
            f"Failed to get dependency health for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        return {
            "success": False,
            "message": "Health check failed",
            "data": {"error": str(e)}
        }
