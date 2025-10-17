"""
API Key Scope-Based Permissions

This module implements granular authorization for API keys based on their scopes.
Scopes follow the principle of least privilege.

Scope Definitions:
- FULL_ACCESS: All operations allowed
- READ_ONLY: Only GET requests allowed (search, list, retrieve)
- UPLOAD_ONLY: Only document uploads and management allowed
"""

import logging
from rest_framework.permissions import BasePermission
from apps.api_keys.models import APIKey

logger = logging.getLogger(__name__)


class IsAuthenticatedOrHasAPIKey(BasePermission):
    """
    Permission class that allows access if the user is authenticated via JWT/session
    OR if they have a valid API key.
    
    This should be used instead of IsAuthenticated when you want to allow both
    traditional authentication and API key authentication.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated (JWT/session)
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            return True
        
        # Check if API key authentication was successful
        if hasattr(request, 'auth_api_key') and request.auth_api_key:
            return True
        
        return False


class HasAPIKeyScope(BasePermission):
    """
    Permission class that checks if the API key has the required scope.
    
    Usage in views:
        permission_classes = [IsAuthenticated, HasAPIKeyScope]
        required_scope = APIKey.Scope.FULL  # or READ_ONLY, UPLOAD_ONLY
    
    If no API key is present (JWT auth), permission is granted.
    If API key is present, scope is checked against required_scope.
    """
    
    def has_permission(self, request, view):
        # If no API key authentication was used, allow (JWT or session auth)
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True
        
        # Get required scope from view
        required_scope = getattr(view, 'required_scope', None)
        if not required_scope:
            # No specific scope required, check if full access
            return api_key.scope == APIKey.Scope.FULL
        
        # Check if API key scope matches required scope
        if api_key.scope == APIKey.Scope.FULL:
            # Full access allows everything
            return True
        
        # Check specific scope requirements
        if api_key.scope == required_scope:
            return True
        
        logger.warning(
            f"API key scope mismatch",
            extra={
                'api_key_id': str(api_key.id),
                'api_key_scope': api_key.scope,
                'required_scope': required_scope,
                'path': request.path,
                'method': request.method
            }
        )
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        API keys can only access resources in their organization.
        """
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True
        
        # Check if object belongs to the same organization
        obj_org = getattr(obj, 'organization', None)
        if obj_org and obj_org != api_key.organization:
            logger.warning(
                f"API key attempted to access resource from different organization",
                extra={
                    'api_key_id': str(api_key.id),
                    'api_key_org': api_key.organization.name,
                    'resource_org': obj_org.name,
                    'resource_type': type(obj).__name__
                }
            )
            return False
        
        return True


class ReadOnlyAPIKeyPermission(BasePermission):
    """
    Permission for read-only operations.
    Only allows GET, HEAD, OPTIONS methods for API keys with READ_ONLY scope.
    """
    
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
    
    def has_permission(self, request, view):
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True  # Not using API key auth
        
        # Full access keys can do anything
        if api_key.scope == APIKey.Scope.FULL:
            return True
        
        # Read-only keys can only use safe methods
        if api_key.scope == APIKey.Scope.READ_ONLY:
            is_safe = request.method in self.SAFE_METHODS
            if not is_safe:
                logger.warning(
                    f"Read-only API key attempted write operation",
                    extra={
                        'api_key_id': str(api_key.id),
                        'method': request.method,
                        'path': request.path
                    }
                )
            return is_safe
        
        # Upload-only keys cannot perform read operations (except their own uploads)
        if api_key.scope == APIKey.Scope.UPLOAD_ONLY:
            return False
        
        return False


class UploadOnlyAPIKeyPermission(BasePermission):
    """
    Permission for upload-only operations.
    Only allows document upload and management operations.
    """
    
    ALLOWED_PATHS = ['/api/documents/', '/api/documents']
    ALLOWED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE', 'GET']
    
    def has_permission(self, request, view):
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True
        
        # Full access keys can do anything
        if api_key.scope == APIKey.Scope.FULL:
            return True
        
        # Upload-only keys can only access document endpoints
        if api_key.scope == APIKey.Scope.UPLOAD_ONLY:
            is_allowed = any(
                request.path.startswith(path) for path in self.ALLOWED_PATHS
            )
            if not is_allowed:
                logger.warning(
                    f"Upload-only API key attempted non-upload operation",
                    extra={
                        'api_key_id': str(api_key.id),
                        'method': request.method,
                        'path': request.path
                    }
                )
            return is_allowed
        
        return False


class ChatAPIKeyPermission(BasePermission):
    """
    Permission specifically for chat endpoints.
    - FULL_ACCESS: Can chat
    - READ_ONLY: Cannot chat (read-only)
    - UPLOAD_ONLY: Cannot chat (upload-only)
    """
    
    def has_permission(self, request, view):
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True  # JWT or session auth
        
        # Only full access keys can use chat endpoints
        can_chat = api_key.scope == APIKey.Scope.FULL
        
        if not can_chat:
            logger.warning(
                f"Non-full-access API key attempted to use chat endpoint",
                extra={
                    'api_key_id': str(api_key.id),
                    'api_key_scope': api_key.scope,
                    'path': request.path,
                    'method': request.method
                }
            )
        
        return can_chat


class SearchAPIKeyPermission(BasePermission):
    """
    Permission for search endpoints.
    - FULL_ACCESS: Can search
    - READ_ONLY: Can search
    - UPLOAD_ONLY: Cannot search
    """
    
    def has_permission(self, request, view):
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True
        
        # Full access and read-only can search
        can_search = api_key.scope in [APIKey.Scope.FULL, APIKey.Scope.READ_ONLY]
        
        if not can_search:
            logger.warning(
                f"Upload-only API key attempted to search",
                extra={
                    'api_key_id': str(api_key.id),
                    'path': request.path
                }
            )
        
        return can_search
