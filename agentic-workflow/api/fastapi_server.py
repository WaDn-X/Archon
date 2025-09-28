"""
FastAPI Server for Zippy-Archon Platform

This module provides a comprehensive REST API for the Zippy-Archon platform
with endpoints for requirements, A/B testing, marketplace, and user management.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# Environment configuration (must be defined before use)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize logger early
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO if ENVIRONMENT == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if ENVIRONMENT == "production" else logging.NullHandler()
    ]
)

# Security logging
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Prometheus metrics with proper registry
try:
    from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    # Create registry to avoid conflicts
    registry = CollectorRegistry()
    # Define metrics with registry
    REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'], registry=registry)
    REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'], registry=registry)
    ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections', registry=registry)
    AI_REQUEST_COUNT = Counter('ai_requests_total', 'Total AI requests', ['provider', 'model'], registry=registry)
    DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections', registry=registry)
    PROMETHEUS_AVAILABLE = True
    logger.info("Prometheus metrics initialized successfully")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available, metrics disabled")

# Redis for caching and rate limiting
try:
    import redis.asyncio as redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    REDIS_AVAILABLE = True
    logger.info("Redis client initialized successfully")
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning("Redis client not available, using in-memory storage")

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Sentry (must be done before other imports)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Configure Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0 if ENVIRONMENT == "production" else 0.1,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        profiles_sample_rate=1.0 if ENVIRONMENT == "production" else 0.1,
        environment=ENVIRONMENT,
        release=os.getenv("RELEASE_VERSION", "1.0.0"),
    )
    logger.info("Sentry monitoring initialized")

from ai.multi_provider_ai import create_multi_provider_system, MultiProviderAISystem
from database.database_factory import initialize_database, get_database_manager
from database.supabase_client import SupabaseManager, DatabaseConfig
from plugins.trust_manager import ZippyTrustManager
from plugins.marketplace import ZippyCoinMarketplace
from testing.enhanced_ab_testing import EnhancedABTesting
from testing.enhanced_rubric import EnhancedRubricScorer

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class GenerateSpecsRequest(BaseModel):
    prompt: str = Field(..., description="Feature description")
    provider: Optional[str] = Field("grok", description="Preferred AI provider")
    version: Optional[str] = Field("v1", description="Prompt version")
    reviewer_pass: Optional[bool] = Field(True, description="Use reviewer pass")

class ABTestRequest(BaseModel):
    prompt: str = Field(..., description="Feature description")
    versions: List[str] = Field(..., description="Versions to test")
    provider: Optional[str] = Field("grok", description="AI provider")
    num_runs: Optional[int] = Field(3, description="Number of test runs")

class MarketplaceListingRequest(BaseModel):
    title: str = Field(..., description="Listing title")
    description: str = Field(..., description="Listing description")
    content: Dict[str, Any] = Field(..., description="Listing content")
    category: str = Field(..., description="Listing category")
    tags: List[str] = Field(default_factory=list, description="Listing tags")
    pricing: Dict[str, Any] = Field(..., description="Pricing information")

class UserRegistrationRequest(BaseModel):
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    wallet_address: str = Field(..., description="Wallet address")

class TrustValidationRequest(BaseModel):
    content: str = Field(..., description="Content to validate")
    content_type: str = Field(..., description="Type of content")

# Response models
class GenerateSpecsResponse(BaseModel):
    success: bool
    provider: str
    version: str
    requirements: Dict[str, Any]
    design: Dict[str, Any]
    tasks: Dict[str, Any]
    metadata: Dict[str, Any]

class ABTestResponse(BaseModel):
    success: bool
    test_id: str
    results: Dict[str, Any]
    winner: str
    comparison_metrics: Dict[str, Any]

class MarketplaceListingResponse(BaseModel):
    success: bool
    listing_id: str
    listing: Dict[str, Any]

class TrustValidationResponse(BaseModel):
    success: bool
    trust_score: float
    trust_level: str
    metrics: Dict[str, Any]
    insights: List[str]

class PlatformStatsResponse(BaseModel):
    total_requirements: int
    total_ab_tests: int
    total_listings: int
    total_users: int
    total_volume: float
    generated_at: str

# Initialize FastAPI app
app = FastAPI(
    title="Zippy-Archon API",
    description="Comprehensive API for the Zippy-Archon platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
# Production-ready CORS configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    # Production: Allow specific domains
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "https://yourdomain.com,https://www.yourdomain.com").split(",")
    allow_credentials = True
else:
    # Development: Allow all for local development
    allowed_origins = ["*"]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight for 24 hours
)

# Metrics Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Metrics collection middleware."""
    if PROMETHEUS_AVAILABLE:
        start_time = time.time()
        ACTIVE_CONNECTIONS.inc()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=str(response.status_code)
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            return response
        finally:
            ACTIVE_CONNECTIONS.dec()
    else:
        return await call_next(request)

# Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/metrics"]:
        return await call_next(request)

    # Get client IP (works with proxies)
    client_ip = request.client.host if request.client else "unknown"

    if is_rate_limited(client_ip):
        # Log rate limit response
        security_logger.warning(f"Rate limit response sent to IP: {client_ip} for path: {request.url.path}")
        return Response(
            content='{"error": "Rate limit exceeded", "retry_after": 60}',
            status_code=429,
            media_type="application/json"
        )

    response = await call_next(request)
    return response

# Security
security = HTTPBearer()
from datetime import timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate Limiting Configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# In-memory rate limiting storage (fallback when Redis is unavailable)
rate_limit_store = defaultdict(list)

# Caching utilities
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

async def cache_get(key: str):
    """Get value from cache."""
    if REDIS_AVAILABLE and redis_client:
        try:
            return await redis_client.get(key)
        except Exception:
            pass
    return None

async def cache_set(key: str, value: str, ttl: int = CACHE_TTL):
    """Set value in cache."""
    if REDIS_AVAILABLE and redis_client:
        try:
            await redis_client.setex(key, ttl, value)
            return True
        except Exception:
            pass
    return False

async def cache_delete(key: str):
    """Delete value from cache."""
    if REDIS_AVAILABLE and redis_client:
        try:
            await redis_client.delete(key)
            return True
        except Exception:
            pass
    return False

# Rate limiting with Redis fallback
async def is_rate_limited(client_ip: str) -> bool:
    """Check if client is rate limited using Redis or in-memory storage."""
    current_time = int(time.time())
    window_start = current_time - RATE_LIMIT_WINDOW
    key = f"rate_limit:{client_ip}"

    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis for rate limiting
            # Clean old requests and count current ones
            await redis_client.zremrangebyscore(key, '-inf', window_start)
            request_count = await redis_client.zcard(key)

            if request_count >= RATE_LIMIT_REQUESTS:
                # Log rate limit violation
                security_logger.warning(f"Rate limit exceeded for IP: {client_ip} (Redis)")
                return True

            # Add current request
            await redis_client.zadd(key, {str(current_time): current_time})
            # Set expiration on the key
            await redis_client.expire(key, RATE_LIMIT_WINDOW)
            return False
        else:
            # Fallback to in-memory storage
            # Clean old requests (older than window)
            rate_limit_store[client_ip] = [
                timestamp for timestamp in rate_limit_store[client_ip]
                if current_time - timestamp < RATE_LIMIT_WINDOW
            ]

            # Check if under limit
            if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
                # Log rate limit violation
                security_logger.warning(f"Rate limit exceeded for IP: {client_ip} (Memory)")
                return True

            # Add current request
            rate_limit_store[client_ip].append(current_time)
            return False

    except Exception as e:
        logger.warning(f"Rate limiting error: {e}, allowing request")
        return False

# Global instances
ai_system: Optional[MultiProviderAISystem] = None
db_manager: Optional[SupabaseManager] = None
trust_manager: Optional[ZippyTrustManager] = None
marketplace: Optional[ZippyCoinMarketplace] = None
ab_testing: Optional[EnhancedABTesting] = None
rubric_scorer: Optional[EnhancedRubricScorer] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global ai_system, db_manager, trust_manager, marketplace, ab_testing, rubric_scorer

    try:
        # Initialize database first (required by other services)
        logger.info("Initializing database...")
        db_manager = await initialize_database()

        # Initialize AI system
        ai_system = create_multi_provider_system()
        logger.info("AI system initialized")

        # Initialize other services
        trust_manager = ZippyTrustManager()
        marketplace = ZippyCoinMarketplace()
        ab_testing = EnhancedABTesting()
        rubric_scorer = EnhancedRubricScorer()

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Zippy-Archon API")

# JWT Utility Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username, "user_id": payload.get("user_id")}
    except JWTError:
        return None

# Dependency injection
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if payload is None:
            # Log failed authentication attempt
            security_logger.warning(f"Failed authentication attempt - invalid token")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log successful authentication
        security_logger.info(f"Successful authentication for user: {payload.get('username', 'unknown')}")
        return payload
    except JWTError as e:
        # Log JWT error
        security_logger.error(f"JWT error during authentication: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Authentication models
class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - getattr(app, 'start_time', time.time()),
        "version": os.getenv("RELEASE_VERSION", "1.0.0"),
        "environment": ENVIRONMENT,
        "services": {
            "ai_system": ai_system is not None,
            "database": db_manager is not None,
            "trust_manager": trust_manager is not None,
            "marketplace": marketplace is not None,
            "prometheus": PROMETHEUS_AVAILABLE,
            "sentry": SENTRY_DSN is not None,
            "redis": REDIS_AVAILABLE
        }
    }

    # Check database connectivity
    if db_manager:
        try:
            db_health = await db_manager.test_connection()
            health_status["services"]["database_connected"] = db_health
        except Exception as e:
            health_status["services"]["database_error"] = str(e)
            health_status["status"] = "degraded"

    # Check AI providers
    if ai_system:
        available_providers = ai_system.get_available_providers()
        health_status["ai_providers"] = {
            "available": available_providers,
            "count": len(available_providers)
        }

    return health_status

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not PROMETHEUS_AVAILABLE:
        return {"error": "Prometheus metrics not available"}

    # Update database connections metric
    if db_manager and hasattr(db_manager, 'client'):
        try:
            # This is a simplified metric - in production you'd track actual connection pool
            DATABASE_CONNECTIONS.set(1)
        except:
            DATABASE_CONNECTIONS.set(0)

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Authenticate user and return JWT token."""
    try:
        # In production, validate against database
        # For now, accept any username/password combination
        if not login_data.username or not login_data.password:
            raise HTTPException(
                status_code=400,
                detail="Username and password are required"
            )

        # Create JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": login_data.username, "user_id": f"user_{login_data.username}"},
            expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.post("/auth/register")
async def register(user_data: UserRegistrationRequest):
    """Register a new user."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")

        # Check if user already exists
        existing_user = await db_manager.get_user_by_wallet(user_data.wallet_address)
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        # Hash password if provided (for future enhancement)
        hashed_password = None
        if hasattr(user_data, 'password'):
            hashed_password = pwd_context.hash(user_data.password)

        # Create user
        user_data_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "wallet_address": user_data.wallet_address,
            "hashed_password": hashed_password,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "zippycoin_balance": 0.0
        }

        user = await db_manager.create_user(user_data_dict)

        return {
            "success": True,
            "user_id": user["id"],
            "message": "User registered successfully"
        }

    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Requirements endpoints
@app.post("/api/v1/specs/generate", response_model=GenerateSpecsResponse)
async def generate_specs(
    request: GenerateSpecsRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate specifications using AI."""
    try:
        if not ai_system:
            raise HTTPException(status_code=503, detail="AI system not available")
        
        # Validate and sanitize input
        try:
            sanitized_prompt = validate_and_sanitize_input(request.prompt, max_length=5000)
        except ValueError as e:
            # Log input validation failure
            security_logger.warning(f"Input validation failed for generate_specs: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
        
        # Generate specs
        result = await ai_system.generate_specs(
            prompt=sanitized_prompt,
            provider=request.provider,
            version=request.version,
            reviewer_pass=request.reviewer_pass
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Generation failed'))
        
        # Store in database
        if db_manager:
            background_tasks.add_task(
                store_generation_result,
                result,
                current_user["user_id"]
            )
        
        return GenerateSpecsResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to generate specs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/specs/{spec_id}")
async def get_specs(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specifications by ID."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        spec = await db_manager.get_requirement(spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specification not found")
        
        return spec
        
    except Exception as e:
        logger.error(f"Failed to get specs {spec_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/specs")
async def list_specs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List specifications."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        specs = await db_manager.list_requirements(limit=limit)
        return {
            "specs": specs,
            "total": len(specs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list specs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# A/B Testing endpoints
@app.post("/api/v1/ab-test/run", response_model=ABTestResponse)
async def run_ab_test(
    request: ABTestRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Run A/B test comparing different prompt versions."""
    try:
        if not ab_testing or not ai_system:
            raise HTTPException(status_code=503, detail="A/B testing system not available")
        
        # Validate and sanitize input
        try:
            sanitized_prompt = validate_and_sanitize_input(request.prompt, max_length=5000)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
        
        # Run A/B test
        result = await ab_testing.run_test(
            prompt=sanitized_prompt,
            versions=request.versions,
            provider=request.provider,
            num_runs=request.num_runs
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'A/B test failed'))
        
        # Store in database
        if db_manager:
            background_tasks.add_task(
                store_ab_test_result,
                result,
                current_user["user_id"]
            )
        
        return ABTestResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to run A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ab-test/{test_id}")
async def get_ab_test(
    test_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get A/B test results by ID."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        test = await db_manager.get_ab_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return test
        
    except Exception as e:
        logger.error(f"Failed to get A/B test {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ab-test")
async def list_ab_tests(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List A/B tests."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        tests = await db_manager.list_ab_tests(limit=limit)
        return {
            "tests": tests,
            "total": len(tests),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list A/B tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Marketplace endpoints
@app.post("/api/v1/marketplace/listings", response_model=MarketplaceListingResponse)
async def create_marketplace_listing(
    request: MarketplaceListingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new marketplace listing."""
    try:
        if not marketplace or not db_manager:
            raise HTTPException(status_code=503, detail="Marketplace not available")
        
        # Validate content with ZippyTrust
        if trust_manager:
            trust_result = await trust_manager.validate_content(
                content=json.dumps(request.content),
                content_type=request.category
            )
            
            if trust_result.trust_level == "low":
                raise HTTPException(status_code=400, detail="Content failed trust validation")
        
        # Create listing
        listing_data = {
            "title": request.title,
            "description": request.description,
            "content": request.content,
            "category": request.category,
            "tags": request.tags,
            "pricing": request.pricing,
            "author_id": current_user["user_id"],
            "author_wallet": current_user["wallet_address"],
            "trust_score": trust_result.trust_score if trust_manager else 0.8
        }
        
        listing = await db_manager.create_marketplace_listing(listing_data)
        
        return MarketplaceListingResponse(
            success=True,
            listing_id=listing["id"],
            listing=listing
        )
        
    except Exception as e:
        logger.error(f"Failed to create marketplace listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/marketplace/listings/{listing_id}")
async def get_marketplace_listing(
    listing_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get marketplace listing by ID."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        listing = await db_manager.get_marketplace_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return listing
        
    except Exception as e:
        logger.error(f"Failed to get marketplace listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/marketplace/listings")
async def search_marketplace_listings(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    min_trust_score: Optional[float] = Query(0.0, ge=0.0, le=1.0, description="Minimum trust score"),
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search marketplace listings."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        listings = await db_manager.search_marketplace_listings(
            query=query,
            category=category,
            min_trust_score=min_trust_score,
            limit=limit
        )
        
        return {
            "listings": listings,
            "total": len(listings),
            "query": query,
            "category": category,
            "min_trust_score": min_trust_score
        }
        
    except Exception as e:
        logger.error(f"Failed to search marketplace listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/marketplace/listings/{listing_id}/purchase")
async def purchase_listing(
    listing_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Purchase a marketplace listing."""
    try:
        if not marketplace or not db_manager:
            raise HTTPException(status_code=503, detail="Marketplace not available")
        
        # Get listing
        listing = await db_manager.get_marketplace_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Process purchase
        purchase_result = await marketplace.process_purchase(
            listing_id=listing_id,
            buyer_id=current_user["user_id"],
            buyer_wallet=current_user["wallet_address"],
            price=listing["pricing"]["price"]
        )
        
        if not purchase_result["success"]:
            raise HTTPException(status_code=400, detail=purchase_result["error"])
        
        return purchase_result
        
    except Exception as e:
        logger.error(f"Failed to purchase listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Input validation utilities
def validate_and_sanitize_input(input_data: str, max_length: int = 1000) -> str:
    """Validate and sanitize user input to prevent injection attacks."""
    if not input_data or not isinstance(input_data, str):
        raise ValueError("Input must be a non-empty string")
    
    if len(input_data) > max_length:
        raise ValueError(f"Input too long. Maximum length: {max_length}")
    
    # Remove potentially dangerous characters
    dangerous_patterns = [
        '<script>', '</script>', 'javascript:', 'vbscript:', 'onload=',
        'onerror=', 'onclick=', 'onmouseover=', 'eval(', 'exec(',
        'document.cookie', 'window.location', 'localStorage', 'sessionStorage'
    ]
    
    sanitized = input_data
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern.lower(), '')
        sanitized = sanitized.replace(pattern.upper(), '')
    
    # Remove HTML tags
    import re
    sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Remove SQL injection patterns
    sql_patterns = [
        'union select', 'drop table', 'delete from', 'insert into',
        'update set', 'alter table', 'create table', 'exec sp_'
    ]
    
    for pattern in sql_patterns:
        sanitized = sanitized.replace(pattern.lower(), '')
        sanitized = sanitized.replace(pattern.upper(), '')
    
    return sanitized.strip()

def validate_file_upload(filename: str, allowed_extensions: List[str] = None) -> bool:
    """Validate file uploads to prevent malicious files."""
    if not allowed_extensions:
        allowed_extensions = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml']
    
    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in allowed_extensions:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check filename length
    if len(filename) > 255:
        return False
    
    return True

# Trust validation endpoints
@app.post("/api/v1/trust/validate", response_model=TrustValidationResponse)
async def validate_content(
    request: TrustValidationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate content using ZippyTrust."""
    try:
        if not trust_manager or not rubric_scorer:
            raise HTTPException(status_code=503, detail="Trust validation not available")
        
        # Score content with enhanced rubric
        score = await rubric_scorer.score_content(
            content=request.content,
            kind=request.content_type
        )
        
        # Generate trust insights
        insights = await rubric_scorer.generate_trust_insights(score)
        
        return TrustValidationResponse(
            success=True,
            trust_score=score.total,
            trust_level=score.trust_level,
            metrics={
                "clarity": score.clarity,
                "structure": score.structure,
                "testability": score.testability,
                "conformity": score.conformity,
                "security_score": score.security_score,
                "code_quality": score.code_quality,
                "documentation_quality": score.documentation_quality,
                "community_trust": score.community_trust
            },
            insights=insights
        )
        
    except Exception as e:
        logger.error(f"Failed to validate content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User management endpoints
@app.post("/api/v1/users/register")
async def register_user(request: UserRegistrationRequest):
    """Register a new user."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Check if user already exists
        existing_user = await db_manager.get_user_by_wallet(request.wallet_address)
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Validate and sanitize input
        try:
            sanitized_username = validate_and_sanitize_input(request.username, max_length=100)
            sanitized_email = validate_and_sanitize_input(request.email, max_length=255)
            sanitized_wallet = validate_and_sanitize_input(request.wallet_address, max_length=100)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
        
        # Create user
        user_data = {
            "username": sanitized_username,
            "email": sanitized_email,
            "wallet_address": sanitized_wallet
        }
        
        user = await db_manager.create_user(user_data)
        
        return {
            "success": True,
            "user_id": user["id"],
            "message": "User registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user by ID."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        user = await db_manager.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/{user_id}/balance")
async def get_user_balance(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's ZippyCoin balance."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        user = await db_manager.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "balance": user["zippycoin_balance"],
            "currency": "ZippyCoin"
        }
        
    except Exception as e:
        logger.error(f"Failed to get user balance {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/api/v1/analytics/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get platform statistics."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        stats = await db_manager.get_platform_stats()
        return PlatformStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get platform stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/ai-usage")
async def get_ai_usage_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get AI usage statistics."""
    try:
        if not ai_system:
            raise HTTPException(status_code=503, detail="AI system not available")
        
        usage_stats = ai_system.get_usage_stats()
        return usage_stats
        
    except Exception as e:
        logger.error(f"Failed to get AI usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def store_generation_result(result: Dict[str, Any], user_id: str):
    """Store generation result in database."""
    try:
        if db_manager:
            await db_manager.create_requirement({
                "user_id": user_id,
                "prompt": result.get("prompt", ""),
                "provider": result["provider"],
                "version": result["version"],
                "requirements_content": result["requirements"]["content"],
                "design_content": result["design"]["content"],
                "tasks_content": result["tasks"]["content"],
                "metadata": result["metadata"]
            })
    except Exception as e:
        logger.error(f"Failed to store generation result: {e}")

async def store_ab_test_result(result: Dict[str, Any], user_id: str):
    """Store A/B test result in database."""
    try:
        if db_manager:
            await db_manager.create_ab_test({
                "user_id": user_id,
                "prompt": result.get("prompt", ""),
                "versions": result["versions"],
                "results": result["results"],
                "winner": result["winner"],
                "comparison_metrics": result["comparison_metrics"]
            })
    except Exception as e:
        logger.error(f"Failed to store A/B test result: {e}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return {"error": "Resource not found", "detail": str(exc)}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return {"error": "Internal server error", "detail": str(exc)}

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
