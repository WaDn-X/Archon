"""
FastAPI Backend for Archon Knowledge Engine

This is the main entry point for the Archon backend API.
It uses a modular approach with separate API modules for different functionality.

Modules:
- settings_api: Settings and credentials management
- mcp_api: MCP server management and WebSocket streaming
- knowledge_api: Knowledge base, crawling, and RAG operations
- projects_api: Project and task management with streaming
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routes.agent_chat_api import router as agent_chat_router
from .api_routes.bug_report_api import router as bug_report_router
from .api_routes.coverage_api import router as coverage_router
from .api_routes.internal_api import router as internal_router
from .api_routes.knowledge_api import router as knowledge_router
from .api_routes.mcp_api import router as mcp_router
from .api_routes.projects_api import router as projects_router

# Import Socket.IO handlers to ensure they're registered
from .api_routes import socketio_handlers  # This registers all Socket.IO event handlers

# Import modular API routers
from .api_routes.settings_api import router as settings_router
from .api_routes.tests_api import router as tests_router

# Import Logfire configuration
from .config.logfire_config import api_logger, setup_logfire
from .services.background_task_manager import cleanup_task_manager
from .services.crawler_manager import cleanup_crawler, initialize_crawler

# Import utilities and core classes
from .services.credential_service import initialize_credentials

# Import Socket.IO integration
from .socketio_app import create_socketio_app

# Import missing dependencies that the modular APIs need
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig
except ImportError:
    # These are optional dependencies for full functionality
    AsyncWebCrawler = None
    BrowserConfig = None

# Logger will be initialized after credentials are loaded
logger = logging.getLogger(__name__)

# Set up logging configuration to reduce noise

# Override uvicorn's access log format to be less verbose
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.setLevel(logging.WARNING)  # Only log warnings and errors, not every request

# CrawlingContext has been replaced by CrawlerManager in services/crawler_manager.py

# Global flag to track if initialization is complete
_initialization_complete = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks."""
    global _initialization_complete
    _initialization_complete = False

    # Startup
    logger.info("🚀 Starting Archon backend...")

    try:
        # Validate configuration FIRST - check for anon vs service key
        from .config.config import get_config

        get_config()  # This will raise ConfigurationError if anon key detected

        # Initialize credentials from database FIRST - this is the foundation for everything else
        await initialize_credentials()

        # Now that credentials are loaded, we can properly initialize logging
        # This must happen AFTER credentials so LOGFIRE_ENABLED is set from database
        setup_logfire(service_name="archon-backend")

        # Now we can safely use the logger
        logger.info("✅ Credentials initialized")
        api_logger.info("🔥 Logfire initialized for backend")

        # Initialize crawling context
        try:
            await initialize_crawler()
        except Exception as e:
            api_logger.warning(f"Could not fully initialize crawling context: {str(e)}")

        # Make crawling context available to modules
        # Crawler is now managed by CrawlerManager

        # Initialize Socket.IO services
        try:
            # Import API modules to register their Socket.IO handlers
            api_logger.info("✅ Socket.IO handlers imported from API modules")
        except Exception as e:
            api_logger.warning(f"Could not initialize Socket.IO services: {e}")

        # Initialize prompt service
        try:
            from .services.prompt_service import prompt_service

            await prompt_service.load_prompts()
            api_logger.info("✅ Prompt service initialized")
        except Exception as e:
            api_logger.warning(f"Could not initialize prompt service: {e}")

        # Set the main event loop for background tasks
        try:
            from .services.background_task_manager import get_task_manager

            task_manager = get_task_manager()
            current_loop = asyncio.get_running_loop()
            task_manager.set_main_loop(current_loop)
            api_logger.info("✅ Main event loop set for background tasks")
        except Exception as e:
            api_logger.warning(f"Could not set main event loop: {e}")

        # MCP Client functionality removed from architecture
        # Agents now use MCP tools directly

        # Start Phase 3 services
        try:
            api_logger.info("🚀 Starting Phase 3 services...")

            # Start real-time collaboration service
            from .services.realtime_collaboration_service import realtime_collaboration_service
            await realtime_collaboration_service.start()
            api_logger.info("✅ Real-time collaboration service started")

            # Initialize other Phase 3 services (they don't need async startup)
            from .services.task_prioritization_service import task_prioritization_service
            from .services.smart_suggestions_service import smart_suggestions_service
            from .services.task_dependency_service import task_dependency_service
            from .services.progress_tracking_service import progress_tracking_service
            from .services.team_collaboration_service import team_collaboration_service

            api_logger.info("✅ All Phase 3 services initialized")

        except Exception as e:
            api_logger.warning(f"Could not initialize Phase 3 services: {e}")

        # Mark initialization as complete
        _initialization_complete = True
        api_logger.info("🎉 Archon backend started successfully!")

    except Exception as e:
        api_logger.error(f"❌ Failed to start backend: {str(e)}")
        raise

    yield

    # Shutdown
    _initialization_complete = False
    api_logger.info("🛑 Shutting down Archon backend...")

    try:
        # MCP Client cleanup not needed

        # Cleanup crawling context
        try:
            await cleanup_crawler()
        except Exception as e:
            api_logger.warning("Could not cleanup crawling context", error=str(e))

        # Cleanup background task manager
        try:
            await cleanup_task_manager()
            api_logger.info("Background task manager cleaned up")
        except Exception as e:
            api_logger.warning("Could not cleanup background task manager", error=str(e))

        # Stop Phase 3 services
        try:
            from .services.realtime_collaboration_service import realtime_collaboration_service
            await realtime_collaboration_service.stop()
            api_logger.info("Phase 3 services stopped")
        except Exception as e:
            api_logger.warning(f"Could not stop Phase 3 services: {e}")

        api_logger.info("✅ Cleanup completed")

    except Exception as e:
        api_logger.error(f"❌ Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="Archon Knowledge Engine API",
    description="Backend API for the Archon knowledge management and project automation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing WebSocket issue
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import middleware
from .middleware.auth_middleware import (
    AuthMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware
)

# Initialize middleware
auth_middleware = AuthMiddleware()
rate_limit_middleware = RateLimitMiddleware()
security_headers_middleware = SecurityHeadersMiddleware()
request_logging_middleware = RequestLoggingMiddleware()
error_handling_middleware = ErrorHandlingMiddleware()

# Add comprehensive middleware stack
@app.middleware("http")
async def error_handling(request, call_next):
    return await error_handling_middleware(request, call_next)

@app.middleware("http")
async def security_headers(request, call_next):
    return await security_headers_middleware(request, call_next)

@app.middleware("http")
async def rate_limiting(request, call_next):
    return await rate_limit_middleware(request, call_next)

@app.middleware("http")
async def authentication(request, call_next):
    return await auth_middleware(request, call_next)

@app.middleware("http")
async def request_logging(request, call_next):
    return await request_logging_middleware(request, call_next)


# Include API routers
app.include_router(settings_router)
app.include_router(mcp_router)
# app.include_router(mcp_client_router)  # Removed - not part of new architecture
app.include_router(knowledge_router)
app.include_router(projects_router)
app.include_router(tests_router)
app.include_router(agent_chat_router)
app.include_router(internal_router)
app.include_router(coverage_router)
app.include_router(bug_report_router)

# Include new Phase 3 API routers
from .api.task_prioritization_api import router as task_prioritization_router
from .api.realtime_collaboration_api import router as realtime_collaboration_router
from .api.smart_suggestions_api import router as smart_suggestions_router
from .api.task_dependency_api import router as task_dependency_router
from .api.progress_tracking_api import router as progress_tracking_router
from .api.team_collaboration_api import router as team_collaboration_router

app.include_router(task_prioritization_router)
app.include_router(realtime_collaboration_router)
app.include_router(smart_suggestions_router)
app.include_router(task_dependency_router)
app.include_router(progress_tracking_router)
app.include_router(team_collaboration_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Archon Knowledge Engine API",
        "version": "1.0.0",
        "description": "Backend API for knowledge management and project automation",
        "status": "healthy",
        "modules": ["settings", "mcp", "mcp-clients", "knowledge", "projects"],
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that indicates true readiness including credential loading."""
    from datetime import datetime

    # Check if initialization is complete
    if not _initialization_complete:
        return {
            "status": "initializing",
            "service": "archon-backend",
            "timestamp": datetime.now().isoformat(),
            "message": "Backend is starting up, credentials loading...",
            "ready": False,
        }

    return {
        "status": "healthy",
        "service": "archon-backend",
        "timestamp": datetime.now().isoformat(),
        "ready": True,
        "credentials_loaded": True,
    }


# API health check endpoint (alias for /health at /api/health)
@app.get("/api/health")
async def api_health_check():
    """API health check endpoint - alias for /health."""
    return await health_check()


# Create Socket.IO app wrapper
# This wraps the FastAPI app with Socket.IO functionality
socket_app = create_socketio_app(app)

# Export the socket_app for uvicorn to use
# The socket_app still handles all FastAPI routes, but also adds Socket.IO support


def main():
    """Main entry point for running the server."""
    import uvicorn

    # Require ARCHON_SERVER_PORT to be set
    server_port = os.getenv("ARCHON_SERVER_PORT")
    if not server_port:
        raise ValueError(
            "ARCHON_SERVER_PORT environment variable is required. "
            "Please set it in your .env file or environment. "
            "Default value: 8181"
        )

    uvicorn.run(
        "src.server.main:socket_app",
        host="0.0.0.0",
        port=int(server_port),
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
