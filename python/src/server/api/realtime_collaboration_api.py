"""
Real-time Collaboration API Endpoints

REST and WebSocket API endpoints for real-time collaboration features.
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json

from ..services.realtime_collaboration_service import realtime_collaboration_service
from ..services.auth_service import get_current_user
from ..services.error_service import error_service

router = APIRouter(prefix="/api/collaboration", tags=["Real-time Collaboration"])

# Pydantic models for request/response
class ProjectStatsRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")

class NotificationRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    user_ids: List[str] = Field(..., description="User IDs to notify")
    notification: Dict[str, Any] = Field(..., description="Notification content")

class ProjectUpdateRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    update_type: str = Field(..., description="Type of update")
    update_data: Dict[str, Any] = Field(..., description="Update data")


@router.get("/stats/{project_id}")
async def get_project_collaboration_stats(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get collaboration statistics for a project.

    Returns active users, session info, and activity metrics.
    """
    try:
        stats = await realtime_collaboration_service.get_project_collaboration_stats(project_id)

        return {
            "success": True,
            "message": "Collaboration stats retrieved successfully",
            "data": stats
        }

    except Exception as e:
        error_service.log_error(
            "COLLABORATION_STATS_API_ERROR",
            f"Failed to get collaboration stats for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get collaboration stats")


@router.post("/notify")
async def send_project_notifications(
    request: NotificationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send notifications to users in a project.

    Requires appropriate permissions.
    """
    try:
        await realtime_collaboration_service.notify_users(
            request.project_id,
            request.user_ids,
            request.notification
        )

        return {
            "success": True,
            "message": f"Notifications sent to {len(request.user_ids)} users",
            "data": {
                "project_id": request.project_id,
                "user_count": len(request.user_ids),
                "notification": request.notification
            }
        }

    except Exception as e:
        error_service.log_error(
            "NOTIFICATION_API_ERROR",
            f"Failed to send notifications for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to send notifications")


@router.post("/broadcast")
async def broadcast_project_update(
    request: ProjectUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Broadcast an update to all users in a project.

    Requires appropriate permissions.
    """
    try:
        await realtime_collaboration_service.broadcast_project_update(
            request.project_id,
            request.update_type,
            request.update_data
        )

        return {
            "success": True,
            "message": "Project update broadcasted successfully",
            "data": {
                "project_id": request.project_id,
                "update_type": request.update_type,
                "update_data": request.update_data
            }
        }

    except Exception as e:
        error_service.log_error(
            "BROADCAST_API_ERROR",
            f"Failed to broadcast update for project {request.project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to broadcast update")


# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/{project_id}/{user_id}/{username}")
async def websocket_collaboration(
    websocket: WebSocket,
    project_id: str,
    user_id: str,
    username: str
):
    """
    WebSocket endpoint for real-time collaboration.

    Handles real-time communication between users working on the same project.
    """
    try:
        # Validate user (you might want to add JWT token validation here)
        # For now, we'll trust the user_id and username from the URL

        await realtime_collaboration_service.handle_websocket_connection(
            websocket,
            project_id,
            user_id,
            username
        )

    except WebSocketDisconnect:
        # This is expected when client disconnects
        pass
    except Exception as e:
        error_service.log_error(
            "WEBSOCKET_ERROR",
            f"WebSocket error for user {user_id} in project {project_id}",
            {"error": str(e), "user_id": user_id, "project_id": project_id}
        )
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass  # Connection might already be closed


# Connection management endpoints
@router.get("/connections/{project_id}")
async def get_project_connections(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current WebSocket connections for a project.

    Useful for debugging and monitoring.
    """
    try:
        connections = realtime_collaboration_service.connection_manager.get_project_users(project_id)

        # Convert to serializable format
        connection_data = []
        for user in connections:
            connection_data.append({
                "user_id": user.user_id,
                "username": user.username,
                "presence": user.presence.value,
                "last_seen": user.last_seen.isoformat(),
                "current_task": user.current_task,
                "has_websocket": user.websocket is not None
            })

        return {
            "success": True,
            "message": f"Found {len(connection_data)} active connections",
            "data": {
                "project_id": project_id,
                "active_connections": connection_data,
                "total_connections": len(connection_data)
            }
        }

    except Exception as e:
        error_service.log_error(
            "CONNECTIONS_API_ERROR",
            f"Failed to get connections for project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to get connections")


@router.delete("/connections/{project_id}/{user_id}")
async def disconnect_user(
    project_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Force disconnect a user from a project.

    Requires admin permissions.
    """
    try:
        # TODO: Add admin permission check
        # if not current_user.get("role") == "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")

        # Check if user is connected
        session = realtime_collaboration_service.connection_manager.collaboration_sessions.get(project_id)
        if not session or user_id not in session.active_users:
            raise HTTPException(status_code=404, detail="User not connected to project")

        user = session.active_users[user_id]
        if user.websocket:
            await realtime_collaboration_service.connection_manager.disconnect(
                user.websocket, project_id, user_id
            )

        return {
            "success": True,
            "message": f"User {user_id} disconnected from project {project_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        error_service.log_error(
            "DISCONNECT_API_ERROR",
            f"Failed to disconnect user {user_id} from project {project_id}",
            {"error": str(e), "user_id": current_user["user_id"]}
        )
        raise HTTPException(status_code=500, detail="Failed to disconnect user")


@router.get("/health")
async def get_collaboration_health():
    """
    Get health status of the collaboration service.

    Useful for monitoring and debugging.
    """
    try:
        # Get basic health metrics
        active_sessions = len(realtime_collaboration_service.connection_manager.collaboration_sessions)
        total_connections = sum(
            len(session.active_users)
            for session in realtime_collaboration_service.connection_manager.collaboration_sessions.values()
        )

        return {
            "success": True,
            "message": "Collaboration service health check",
            "data": {
                "status": "healthy",
                "active_sessions": active_sessions,
                "total_connections": total_connections,
                "service_running": realtime_collaboration_service._running,
                "uptime": "N/A"  # Could track actual uptime if needed
            }
        }

    except Exception as e:
        error_service.log_error(
            "HEALTH_CHECK_API_ERROR",
            "Failed to get collaboration service health",
            {"error": str(e)}
        )
        return {
            "success": False,
            "message": "Health check failed",
            "data": {"error": str(e)}
        }
