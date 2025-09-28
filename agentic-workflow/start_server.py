#!/usr/bin/env python3
"""
Startup Script for Zippy-Archon Platform

This script initializes and starts the complete Zippy-Archon platform
with all services including the FastAPI server, database connections,
and background tasks.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional
import uvicorn
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "startup.log")
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "JWT_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        return False
    
    return True

def check_ai_providers():
    """Check if at least one AI provider is configured."""
    ai_providers = [
        "XAI_API_KEY",
        "OPENAI_API_KEY", 
        "ANTHROPIC_API_KEY",
        "ZIPPY_API_KEY"
    ]
    
    configured_providers = []
    for provider in ai_providers:
        if os.getenv(provider):
            configured_providers.append(provider.replace("_API_KEY", ""))
    
    if not configured_providers:
        logger.warning("No AI providers configured. The platform will work but AI features will be limited.")
        logger.info("Configure at least one of: XAI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, ZIPPY_API_KEY")
    else:
        logger.info(f"Configured AI providers: {configured_providers}")
    
    return True

async def test_database_connection():
    """Test database connection."""
    try:
        from database.supabase_client import create_supabase_manager
        
        db_manager = create_supabase_manager()
        is_connected = await db_manager.test_connection()
        
        if is_connected:
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.error("❌ Database connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False

async def test_ai_system():
    """Test AI system initialization."""
    try:
        from ai.multi_provider_ai import create_multi_provider_system
        
        ai_system = create_multi_provider_system()
        available_providers = ai_system.get_available_providers()
        
        if available_providers:
            logger.info(f"✅ AI system initialized with providers: {available_providers}")
            return True
        else:
            logger.warning("⚠️ AI system initialized but no providers available")
            return True
            
    except Exception as e:
        logger.error(f"❌ AI system initialization error: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        project_root / "logs",
        project_root / "data",
        project_root / "uploads",
        project_root / "exports"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")

def print_startup_banner():
    """Print startup banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Zippy-Archon Platform                    ║
    ║                                                              ║
    ║  🚀 Starting enhanced platform with:                        ║
    ║     • Multi-provider AI integration                         ║
    ║     • ZippyTrust validation                                 ║
    ║     • A/B testing system                                    ║
    ║     • Marketplace with ZippyCoin                            ║
    ║     • Enhanced rubric scoring                               ║
    ║     • Supabase database integration                         ║
    ║                                                              ║
    ║  📖 API Documentation: http://localhost:8686/docs           ║
    ║  🔍 Health Check: http://localhost:8686/health              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def run_startup_checks():
    """Run all startup checks."""
    logger.info("🔍 Running startup checks...")
    
    # Check environment
    if not check_environment():
        return False
    
    # Check AI providers
    check_ai_providers()
    
    # Create directories
    create_directories()
    
    # Test database connection
    if not await test_database_connection():
        logger.warning("⚠️ Continuing without database connection...")
    
    # Test AI system
    if not await test_ai_system():
        logger.warning("⚠️ Continuing without AI system...")
    
    logger.info("✅ Startup checks completed")
    return True

def start_server():
    """Start the FastAPI server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8686"))
    reload = os.getenv("ENABLE_RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "api.fastapi_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

async def main():
    """Main startup function."""
    print_startup_banner()
    
    # Run startup checks
    checks_passed = await run_startup_checks()
    
    if not checks_passed:
        logger.error("❌ Startup checks failed. Please fix the issues and try again.")
        sys.exit(1)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)

