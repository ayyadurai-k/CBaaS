"""
JWT Authentication for gRPC requests.

This module provides JWT-based authentication for Django Socio gRPC,
allowing secure service-to-service communication.
"""
import logging
from typing import Optional, Tuple, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTGRPCAuthentication:
    """
    JWT Authentication class for gRPC requests.
    
    Validates JWT tokens passed in gRPC metadata and returns
    the authenticated user.
    
    Usage in gRPC metadata:
        metadata = (("authorization", "Bearer <token>"),)
    """
    
    def authenticate(self, context) -> Tuple[Optional[Any], Optional[str]]:
        """
        Authenticate the gRPC request using JWT token from metadata.
        
        Args:
            context: gRPC ServicerContext containing request metadata
            
        Returns:
            Tuple of (user, token) if authenticated, (None, None) otherwise
        """
        # Extract authorization header from gRPC metadata
        metadata = dict(context.invocation_metadata()) if context else {}
        auth_header = metadata.get("authorization", "")
        
        if not auth_header:
            return None, None
        
        # Validate Bearer token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed("Invalid authorization header format")
        
        token = parts[1]
        
        try:
            # Use SimpleJWT to validate the token
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
            
            # Validate token
            UntypedToken(token)
            
            # Decode token to get user info
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            return user, token
            
        except (TokenError, InvalidToken) as e:
            logger.warning(f"gRPC JWT authentication failed: {str(e)}")
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"gRPC authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed("Authentication error")
    
    def authenticate_header(self, request) -> str:
        """
        Return the authentication header for 401 responses.
        """
        return "Bearer"


class ServiceAccountAuthentication:
    """
    Service Account Authentication for internal service-to-service calls.
    
    Uses pre-shared secrets or API keys for internal communication
    between microservices.
    """
    
    def authenticate(self, context) -> Tuple[Optional[Any], Optional[str]]:
        """
        Authenticate using service account credentials.
        
        Args:
            context: gRPC ServicerContext containing request metadata
            
        Returns:
            Tuple of (service_info, token) if authenticated
        """
        metadata = dict(context.invocation_metadata()) if context else {}
        
        # Check for service API key
        service_key = metadata.get("x-service-key", "")
        
        if not service_key:
            return None, None
        
        # Validate against configured service keys
        valid_keys = getattr(settings, "INTERNAL_SERVICE_KEYS", {})
        
        for service_name, key in valid_keys.items():
            if key == service_key:
                logger.info(f"Service account authenticated: {service_name}")
                return {"service": service_name, "is_internal": True}, service_key
        
        raise exceptions.AuthenticationFailed("Invalid service key")
    
    def authenticate_header(self, request) -> str:
        """Return the authentication header for 401 responses."""
        return "X-Service-Key"
