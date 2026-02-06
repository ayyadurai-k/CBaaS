"""
JWT utilities for cross-service authentication.
These utilities are designed to work independently of Django.
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any
from dataclasses import dataclass


@dataclass
class TokenPayload:
    """Decoded JWT token payload."""
    user_id: str
    organization_id: str | None
    email: str
    role: str
    exp: datetime
    iat: datetime
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        return cls(
            user_id=data.get("user_id", ""),
            organization_id=data.get("organization_id"),
            email=data.get("email", ""),
            role=data.get("role", "member"),
            exp=datetime.fromtimestamp(data.get("exp", 0), tz=timezone.utc),
            iat=datetime.fromtimestamp(data.get("iat", 0), tz=timezone.utc),
        )


class JWTValidator:
    """
    Stateless JWT validator for microservices.
    Each service can validate tokens without calling the Identity service.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def validate_token(self, token: str) -> TokenPayload:
        """
        Validate and decode a JWT token.
        
        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
        )
        return TokenPayload.from_dict(payload)
    
    def create_token(
        self,
        user_id: str,
        email: str,
        role: str,
        organization_id: str | None = None,
        expires_delta: timedelta = timedelta(hours=1),
    ) -> str:
        """Create a new JWT token."""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "organization_id": organization_id,
            "iat": now,
            "exp": now + expires_delta,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class PermissionChecker:
    """Permission checking utilities."""
    
    ROLE_HIERARCHY = {
        "owner": 3,
        "admin": 2,
        "member": 1,
    }
    
    @classmethod
    def has_role(cls, user_role: str, required_role: str) -> bool:
        """Check if user has at least the required role level."""
        user_level = cls.ROLE_HIERARCHY.get(user_role, 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level
    
    @classmethod
    def is_owner(cls, user_role: str) -> bool:
        return user_role == "owner"
    
    @classmethod
    def is_admin_or_above(cls, user_role: str) -> bool:
        return cls.has_role(user_role, "admin")
