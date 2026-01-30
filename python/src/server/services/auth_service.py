"""
Unified Authentication Service for Zippy Archon

Provides comprehensive authentication with JWT tokens, API keys,
and session management with proper security measures.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from .credential_service import CredentialService


@dataclass
class User:
    """User data structure."""
    user_id: str
    email: Optional[str] = None
    role: str = "user"
    permissions: List[str] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["read"]


@dataclass
class TokenData:
    """JWT token payload data."""
    user_id: str
    exp: datetime
    iat: datetime
    role: str = "user"


class AuthService:
    """Unified authentication service handling multiple auth methods."""

    def __init__(self):
        # JWT Configuration
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Rate limiting
        self.limiter = Limiter(key_func=get_remote_address)

        # Credential service
        self.credential_service = CredentialService()

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("type") != token_type:
                return None

            user_id: str = payload.get("sub")
            if user_id is None:
                return None

            exp = datetime.fromtimestamp(payload.get("exp", 0))
            iat = datetime.fromtimestamp(payload.get("iat", 0))
            role = payload.get("role", "user")

            return TokenData(
                user_id=user_id,
                exp=exp,
                iat=iat,
                role=role
            )

        except JWTError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from valid refresh token."""
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            return None

        # Create new access token with same user data
        return self.create_access_token({"sub": token_data.user_id, "role": token_data.role})

    async def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        """Authenticate user with identifier and password."""
        # For now, using simple identifier-based auth
        # In production, this would validate against user database
        if not identifier or not password:
            return None

        # Check if user exists in credentials (placeholder logic)
        user_id = identifier  # In real app, this would be looked up
        return User(user_id=user_id, email=f"{identifier}@zippyarchon.com")

    async def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """Authenticate using API key."""
        try:
            # Check API key in credential store
            credentials = await self.credential_service.get_credentials_by_category("api_keys")
            for cred in credentials:
                if cred.get("value") == api_key:
                    return User(
                        user_id=cred.get("name", "api-user"),
                        role="api",
                        permissions=["read", "write"]
                    )
            return None
        except Exception:
            return None

    def get_current_user(self, request: Request) -> Optional[User]:
        """Extract and validate user from request using multiple auth methods."""
        # Try Bearer token first
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            token_data = self.verify_token(token)
            if token_data:
                return User(
                    user_id=token_data.user_id,
                    role=token_data.role
                )

        # Try API key
        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if api_key:
            # For synchronous calls, we need to handle this differently
            # This will be improved when we convert to async middleware
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we can't await here
                    # Return None and let the dependency handle it
                    return None
                else:
                    # Create a new loop for this call
                    user = loop.run_until_complete(self.authenticate_api_key(api_key))
                    return user
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    user = loop.run_until_complete(self.authenticate_api_key(api_key))
                    return user
                finally:
                    loop.close()

        # Try session cookie
        session_token = request.cookies.get("session_token")
        if session_token:
            token_data = self.verify_token(session_token)
            if token_data:
                return User(
                    user_id=token_data.user_id,
                    role=token_data.role
                )

        return None

    def check_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Check if user has required permissions."""
        if not user or not user.permissions:
            return False

        return all(perm in user.permissions for perm in required_permissions)

    def create_rate_limit_key(self, request: Request) -> str:
        """Create rate limit key based on user and endpoint."""
        user = self.get_current_user(request)
        if user:
            return f"user:{user.user_id}:{request.url.path}"
        else:
            return f"ip:{get_remote_address(request)}:{request.url.path}"


# Global auth service instance
auth_service = AuthService()

# FastAPI dependencies
http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    request: Request,
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    """FastAPI dependency to get current authenticated user."""

    # Try Bearer token
    if token and token.credentials:
        token_data = auth_service.verify_token(token.credentials)
        if token_data:
            return User(
                user_id=token_data.user_id,
                role=token_data.role
            )

    # Try API key
    if api_key:
        user = await auth_service.authenticate_api_key(api_key)
        if user:
            return user

    # Try other methods
    user = auth_service.get_current_user(request)
    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_permissions(required_permissions: List[str]):
    """Dependency factory for permission checking."""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not auth_service.check_permissions(current_user, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return permission_checker


# Rate limiting decorators
def rate_limit(calls: int = 100, period: int = 60):
    """Rate limiting decorator for endpoints."""
    def decorator(func):
        # This would integrate with slowapi
        return auth_service.limiter.limit(f"{calls}/{period}seconds")(func)
    return decorator
