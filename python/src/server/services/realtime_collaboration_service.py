"""
Real-time Collaboration Service

Provides WebSocket-based real-time collaboration features including:
- Live task updates and synchronization
- User presence and activity tracking
- Real-time notifications and messaging
- Collaborative editing capabilities
- Conflict resolution and merge handling
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect
from ..utils import get_enhanced_supabase_client
from .error_service import error_service


class CollaborationEvent(Enum):
    """Types of collaboration events."""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    TASK_UPDATED = "task_updated"
    TASK_CREATED = "task_created"
    TASK_DELETED = "task_deleted"
    COMMENT_ADDED = "comment_added"
    FILE_SHARED = "file_shared"
    CURSOR_MOVED = "cursor_moved"
    TYPING_STARTED = "typing_started"
    TYPING_STOPPED = "typing_stopped"
    PRESENCE_UPDATED = "presence_updated"
    NOTIFICATION_SENT = "notification_sent"


class UserPresence(Enum):
    """User presence states."""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class CollaborativeUser:
    """User information for collaboration."""
    user_id: str
    username: str
    avatar_url: Optional[str] = None
    presence: UserPresence = UserPresence.ONLINE
    last_seen: datetime = field(default_factory=datetime.now)
    current_task: Optional[str] = None
    websocket: Optional[Any] = None


@dataclass
class CollaborationSession:
    """Collaboration session for a project."""
    project_id: str
    active_users: Dict[str, CollaborativeUser] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.now)
    session_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationMessage:
    """Message structure for collaboration events."""
    event_type: CollaborationEvent
    project_id: str
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[str] = None


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> project_id
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        self.message_handlers: Dict[CollaborationEvent, List[Callable]] = {}

    async def connect(self, websocket: WebSocket, project_id: str, user_id: str, username: str):
        """Connect a user to a project collaboration session."""
        try:
            await websocket.accept()

            # Initialize or get collaboration session
            if project_id not in self.collaboration_sessions:
                self.collaboration_sessions[project_id] = CollaborationSession(project_id=project_id)

            session = self.collaboration_sessions[project_id]

            # Add user to session
            collaborative_user = CollaborativeUser(
                user_id=user_id,
                username=username,
                websocket=websocket
            )
            session.active_users[user_id] = collaborative_user
            session.last_activity = datetime.now()

            # Add connection to active connections
            if project_id not in self.active_connections:
                self.active_connections[project_id] = []
            self.active_connections[project_id].append(websocket)

            # Update user session mapping
            self.user_sessions[user_id] = project_id

            # Broadcast user joined event
            await self.broadcast_to_project(
                project_id,
                CollaborationMessage(
                    event_type=CollaborationEvent.USER_JOINED,
                    project_id=project_id,
                    user_id=user_id,
                    data={
                        "username": username,
                        "user_count": len(session.active_users),
                        "active_users": [
                            {
                                "user_id": u.user_id,
                                "username": u.username,
                                "presence": u.presence.value,
                                "current_task": u.current_task
                            }
                            for u in session.active_users.values()
                        ]
                    }
                ),
                exclude_user=user_id
            )

            self.logger.info(f"User {username} ({user_id}) joined project {project_id}")

        except Exception as e:
            self.logger.error(f"Error connecting user {user_id} to project {project_id}: {e}")
            raise

    async def disconnect(self, websocket: WebSocket, project_id: str, user_id: str):
        """Disconnect a user from a project collaboration session."""
        try:
            # Remove connection
            if project_id in self.active_connections:
                self.active_connections[project_id] = [
                    conn for conn in self.active_connections[project_id]
                    if conn != websocket
                ]

                # Clean up empty connection lists
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]

            # Remove user from session
            if project_id in self.collaboration_sessions:
                session = self.collaboration_sessions[project_id]
                if user_id in session.active_users:
                    username = session.active_users[user_id].username
                    del session.active_users[user_id]

                    # Broadcast user left event
                    await self.broadcast_to_project(
                        project_id,
                        CollaborationMessage(
                            event_type=CollaborationEvent.USER_LEFT,
                            project_id=project_id,
                            user_id=user_id,
                            data={
                                "username": username,
                                "user_count": len(session.active_users)
                            }
                        )
                    )

                    self.logger.info(f"User {username} ({user_id}) left project {project_id}")

                # Clean up empty sessions
                if not session.active_users:
                    del self.collaboration_sessions[project_id]

            # Clean up user session mapping
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

        except Exception as e:
            self.logger.error(f"Error disconnecting user {user_id}: {e}")

    async def broadcast_to_project(
        self,
        project_id: str,
        message: CollaborationMessage,
        exclude_user: Optional[str] = None
    ):
        """Broadcast a message to all users in a project."""
        if project_id not in self.active_connections:
            return

        message_dict = {
            "event_type": message.event_type.value,
            "project_id": message.project_id,
            "user_id": message.user_id,
            "data": message.data,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id
        }

        # Send to all connections in the project
        disconnected_connections = []
        for websocket in self.active_connections[project_id]:
            try:
                # Skip if this is the user's own connection (for exclude_user)
                if exclude_user and message.user_id == exclude_user:
                    continue

                await websocket.send_json(message_dict)
            except Exception as e:
                self.logger.warning(f"Failed to send message to websocket: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self._cleanup_disconnected_connection(websocket, project_id)

    async def send_to_user(self, user_id: str, message: CollaborationMessage):
        """Send a message to a specific user."""
        project_id = self.user_sessions.get(user_id)
        if not project_id or project_id not in self.collaboration_sessions:
            return

        session = self.collaboration_sessions[project_id]
        if user_id not in session.active_users:
            return

        user = session.active_users[user_id]
        if not user.websocket:
            return

        try:
            message_dict = {
                "event_type": message.event_type.value,
                "project_id": message.project_id,
                "user_id": message.user_id,
                "data": message.data,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id
            }

            await user.websocket.send_json(message_dict)
        except Exception as e:
            self.logger.warning(f"Failed to send message to user {user_id}: {e}")
            await self._cleanup_disconnected_connection(user.websocket, project_id)

    async def _cleanup_disconnected_connection(self, websocket: WebSocket, project_id: str):
        """Clean up a disconnected WebSocket connection."""
        if project_id in self.active_connections:
            self.active_connections[project_id] = [
                conn for conn in self.active_connections[project_id]
                if conn != websocket
            ]

            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    def get_project_users(self, project_id: str) -> List[CollaborativeUser]:
        """Get all active users in a project."""
        if project_id not in self.collaboration_sessions:
            return []

        session = self.collaboration_sessions[project_id]
        return list(session.active_users.values())

    def get_user_project(self, user_id: str) -> Optional[str]:
        """Get the project ID for a user."""
        return self.user_sessions.get(user_id)

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online."""
        project_id = self.user_sessions.get(user_id)
        if not project_id or project_id not in self.collaboration_sessions:
            return False

        session = self.collaboration_sessions[project_id]
        return user_id in session.active_users


class RealTimeCollaborationService:
    """Main service for real-time collaboration features."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = get_enhanced_supabase_client()
        self.connection_manager = WebSocketConnectionManager()
        self.event_handlers: Dict[CollaborationEvent, List[Callable]] = {}
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the collaboration service."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        self.logger.info("Real-time collaboration service started")

    async def stop(self):
        """Stop the collaboration service."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Real-time collaboration service stopped")

    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        project_id: str,
        user_id: str,
        username: str
    ):
        """Handle a WebSocket connection for collaboration."""
        try:
            # Connect user to project
            await self.connection_manager.connect(websocket, project_id, user_id, username)

            # Main message handling loop
            while self._running:
                try:
                    # Receive message from client
                    data = await websocket.receive_json()
                    message = CollaborationMessage(
                        event_type=CollaborationEvent(data.get("event_type")),
                        project_id=project_id,
                        user_id=user_id,
                        data=data.get("data", {}),
                        message_id=data.get("message_id")
                    )

                    # Handle the message
                    await self._handle_collaboration_message(message)

                except WebSocketDisconnect:
                    self.logger.info(f"WebSocket disconnected for user {user_id}")
                    break
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON received from user {user_id}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error handling websocket message: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in websocket connection handler: {e}")
        finally:
            # Clean up connection
            await self.connection_manager.disconnect(websocket, project_id, user_id)

    async def _handle_collaboration_message(self, message: CollaborationMessage):
        """Handle incoming collaboration messages."""
        try:
            # Update user presence/activity
            await self._update_user_activity(message.user_id, message.project_id)

            # Handle different event types
            if message.event_type == CollaborationEvent.TASK_UPDATED:
                await self._handle_task_update(message)
            elif message.event_type == CollaborationEvent.COMMENT_ADDED:
                await self._handle_comment_added(message)
            elif message.event_type == CollaborationEvent.TYPING_STARTED:
                await self._handle_typing_indicator(message, True)
            elif message.event_type == CollaborationEvent.TYPING_STOPPED:
                await self._handle_typing_indicator(message, False)
            elif message.event_type == CollaborationEvent.CURSOR_MOVED:
                await self._handle_cursor_movement(message)
            elif message.event_type == CollaborationEvent.PRESENCE_UPDATED:
                await self._handle_presence_update(message)

            # Broadcast the message to other users
            await self.connection_manager.broadcast_to_project(
                message.project_id,
                message,
                exclude_user=message.user_id
            )

            # Trigger event handlers
            await self._trigger_event_handlers(message)

        except Exception as e:
            self.logger.error(f"Error handling collaboration message: {e}")

    async def _handle_task_update(self, message: CollaborationMessage):
        """Handle task update events."""
        try:
            task_data = message.data
            task_id = task_data.get("task_id")

            if not task_id:
                return

            # Update task in database
            update_data = {
                "updated_at": datetime.now().isoformat(),
                "updated_by": message.user_id
            }

            # Add any task-specific updates
            for key, value in task_data.items():
                if key not in ["task_id", "event_type"]:
                    update_data[key] = value

            await self.supabase.update(
                "archon_tasks",
                update_data,
                {"id": task_id}
            )

            # Log activity
            await self._log_collaboration_activity(
                message.project_id,
                message.user_id,
                "task_updated",
                {"task_id": task_id, "updates": update_data}
            )

        except Exception as e:
            self.logger.error(f"Error handling task update: {e}")

    async def _handle_comment_added(self, message: CollaborationMessage):
        """Handle comment addition events."""
        try:
            comment_data = message.data
            task_id = comment_data.get("task_id")
            content = comment_data.get("content")

            if not task_id or not content:
                return

            # Save comment to database
            comment_record = {
                "task_id": task_id,
                "user_id": message.user_id,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "project_id": message.project_id
            }

            await self.supabase.insert("archon_comments", comment_record)

            # Log activity
            await self._log_collaboration_activity(
                message.project_id,
                message.user_id,
                "comment_added",
                {"task_id": task_id, "comment_id": None}  # Would be populated after insert
            )

        except Exception as e:
            self.logger.error(f"Error handling comment addition: {e}")

    async def _handle_typing_indicator(self, message: CollaborationMessage, is_typing: bool):
        """Handle typing indicator events."""
        try:
            task_id = message.data.get("task_id")
            if task_id:
                # Update user's typing status in session
                if message.project_id in self.connection_manager.collaboration_sessions:
                    session = self.connection_manager.collaboration_sessions[message.project_id]
                    if message.user_id in session.active_users:
                        user = session.active_users[message.user_id]
                        user.current_task = task_id if is_typing else None

        except Exception as e:
            self.logger.error(f"Error handling typing indicator: {e}")

    async def _handle_cursor_movement(self, message: CollaborationMessage):
        """Handle cursor movement events for collaborative editing."""
        # This would be used for collaborative text editing features
        # For now, just broadcast the cursor position
        pass

    async def _handle_presence_update(self, message: CollaborationMessage):
        """Handle presence update events."""
        try:
            presence_data = message.data
            new_presence = presence_data.get("presence")

            if new_presence and message.project_id in self.connection_manager.collaboration_sessions:
                session = self.connection_manager.collaboration_sessions[message.project_id]
                if message.user_id in session.active_users:
                    user = session.active_users[message.user_id]
                    user.presence = UserPresence(new_presence)
                    user.last_seen = datetime.now()

        except Exception as e:
            self.logger.error(f"Error handling presence update: {e}")

    async def _update_user_activity(self, user_id: str, project_id: str):
        """Update user's last activity timestamp."""
        try:
            if project_id in self.connection_manager.collaboration_sessions:
                session = self.connection_manager.collaboration_sessions[project_id]
                if user_id in session.active_users:
                    session.active_users[user_id].last_seen = datetime.now()
                    session.last_activity = datetime.now()
        except Exception as e:
            self.logger.warning(f"Error updating user activity: {e}")

    async def _log_collaboration_activity(
        self,
        project_id: str,
        user_id: str,
        activity_type: str,
        metadata: Dict[str, Any]
    ):
        """Log collaboration activity for analytics."""
        try:
            activity_record = {
                "project_id": project_id,
                "user_id": user_id,
                "activity_type": activity_type,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }

            await self.supabase.insert("archon_collaboration_activity", activity_record)
        except Exception as e:
            self.logger.warning(f"Error logging collaboration activity: {e}")

    async def _cleanup_inactive_sessions(self):
        """Periodically clean up inactive collaboration sessions."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                current_time = datetime.now()
                inactive_threshold = timedelta(minutes=30)

                # Clean up inactive sessions
                sessions_to_remove = []
                for project_id, session in self.connection_manager.collaboration_sessions.items():
                    if current_time - session.last_activity > inactive_threshold:
                        sessions_to_remove.append(project_id)

                for project_id in sessions_to_remove:
                    self.logger.info(f"Cleaning up inactive session for project {project_id}")
                    del self.connection_manager.collaboration_sessions[project_id]
                    if project_id in self.connection_manager.active_connections:
                        del self.connection_manager.active_connections[project_id]

                # Clean up inactive users
                for project_id, session in list(self.connection_manager.collaboration_sessions.items()):
                    users_to_remove = []
                    for user_id, user in session.active_users.items():
                        if current_time - user.last_seen > inactive_threshold:
                            users_to_remove.append(user_id)

                    for user_id in users_to_remove:
                        self.logger.info(f"Removing inactive user {user_id} from project {project_id}")
                        del session.active_users[user_id]
                        if user_id in self.connection_manager.user_sessions:
                            del self.connection_manager.user_sessions[user_id]

                    # Remove empty sessions
                    if not session.active_users:
                        del self.connection_manager.collaboration_sessions[project_id]

            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    def register_event_handler(self, event_type: CollaborationEvent, handler: Callable):
        """Register an event handler for collaboration events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def _trigger_event_handlers(self, message: CollaborationMessage):
        """Trigger registered event handlers."""
        if message.event_type in self.event_handlers:
            for handler in self.event_handlers[message.event_type]:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")

    async def get_project_collaboration_stats(self, project_id: str) -> Dict[str, Any]:
        """Get collaboration statistics for a project."""
        try:
            if project_id not in self.connection_manager.collaboration_sessions:
                return {
                    "active_users": 0,
                    "total_sessions": 0,
                    "last_activity": None
                }

            session = self.connection_manager.collaboration_sessions[project_id]

            # Get activity stats from database
            activity_stats = await self._get_activity_stats(project_id)

            return {
                "active_users": len(session.active_users),
                "total_sessions": activity_stats.get("total_sessions", 0),
                "last_activity": session.last_activity.isoformat(),
                "user_details": [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "presence": user.presence.value,
                        "last_seen": user.last_seen.isoformat(),
                        "current_task": user.current_task
                    }
                    for user in session.active_users.values()
                ],
                "activity_stats": activity_stats
            }

        except Exception as e:
            self.logger.error(f"Error getting collaboration stats: {e}")
            return {"error": str(e)}

    async def _get_activity_stats(self, project_id: str) -> Dict[str, Any]:
        """Get activity statistics from database."""
        try:
            # This would query the collaboration activity logs
            # For now, return mock data
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "total_comments": 0,
                "most_active_users": [],
                "activity_timeline": []
            }
        except Exception as e:
            self.logger.warning(f"Error getting activity stats: {e}")
            return {}

    async def notify_users(
        self,
        project_id: str,
        user_ids: List[str],
        notification: Dict[str, Any]
    ):
        """Send notifications to specific users in a project."""
        try:
            message = CollaborationMessage(
                event_type=CollaborationEvent.NOTIFICATION_SENT,
                project_id=project_id,
                user_id="system",
                data=notification
            )

            for user_id in user_ids:
                await self.connection_manager.send_to_user(user_id, message)

        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")

    async def broadcast_project_update(
        self,
        project_id: str,
        update_type: str,
        update_data: Dict[str, Any],
        exclude_user: Optional[str] = None
    ):
        """Broadcast a project-wide update."""
        try:
            message = CollaborationMessage(
                event_type=CollaborationEvent.TASK_UPDATED,  # Generic update event
                project_id=project_id,
                user_id="system",
                data={
                    "update_type": update_type,
                    **update_data
                }
            )

            await self.connection_manager.broadcast_to_project(
                project_id,
                message,
                exclude_user=exclude_user
            )

        except Exception as e:
            self.logger.error(f"Error broadcasting project update: {e}")


# Global service instance
realtime_collaboration_service = RealTimeCollaborationService()
