"""
Identity Service Interface

This interface abstracts access to User, Organization, and API Key data.
In Phase 1 (Modular Monolith), it uses Django ORM directly.
In Phase 2+, it will make HTTP calls to the Identity Service.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserData:
    """User data returned by the Identity Service."""
    id: str
    email: str
    name: str
    role: str
    organization_id: Optional[str]
    is_active: bool


@dataclass
class OrganizationData:
    """Organization data returned by the Identity Service."""
    id: str
    name: str
    slug: str
    logo_url: Optional[str]


@dataclass
class APIKeyData:
    """API Key validation result."""
    id: str
    organization_id: str
    scope: str
    is_valid: bool
    rate_limit_per_minute: Optional[int]


class IdentityServiceInterface(ABC):
    """Abstract interface for Identity Service operations."""
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[UserData]:
        """Fetch a user by ID."""
        pass
    
    @abstractmethod
    def get_users_bulk(self, user_ids: list[str]) -> list[UserData]:
        """Fetch multiple users by IDs."""
        pass
    
    @abstractmethod
    def get_organization(self, organization_id: str) -> Optional[OrganizationData]:
        """Fetch an organization by ID."""
        pass
    
    @abstractmethod
    def get_organization_members(self, organization_id: str) -> list[UserData]:
        """Fetch all members of an organization."""
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> Optional[APIKeyData]:
        """Validate an API key and return its metadata."""
        pass


class LocalIdentityService(IdentityServiceInterface):
    """
    Local implementation using Django ORM.
    Used in Phase 1 (Modular Monolith).
    """
    
    def get_user(self, user_id: str) -> Optional[UserData]:
        """Fetch a user by ID using Django ORM."""
        from apps.users.models import User
        
        try:
            user = User.objects.select_related('organization').get(id=user_id)
            return UserData(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role,
                organization_id=str(user.organization_id) if user.organization_id else None,
                is_active=user.is_active,
            )
        except User.DoesNotExist:
            logger.warning(f"User not found: {user_id}")
            return None
    
    def get_users_bulk(self, user_ids: list[str]) -> list[UserData]:
        """Fetch multiple users by IDs."""
        from apps.users.models import User
        
        users = User.objects.filter(id__in=user_ids).select_related('organization')
        return [
            UserData(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role,
                organization_id=str(user.organization_id) if user.organization_id else None,
                is_active=user.is_active,
            )
            for user in users
        ]
    
    def get_organization(self, organization_id: str) -> Optional[OrganizationData]:
        """Fetch an organization by ID."""
        from apps.organizations.models import Organization
        
        try:
            org = Organization.objects.get(id=organization_id)
            logo_url = org.logo.url if org.logo else None
            return OrganizationData(
                id=str(org.id),
                name=org.name,
                slug=org.slug,
                logo_url=logo_url,
            )
        except Organization.DoesNotExist:
            logger.warning(f"Organization not found: {organization_id}")
            return None
    
    def get_organization_members(self, organization_id: str) -> list[UserData]:
        """Fetch all members of an organization."""
        from apps.users.models import User
        
        users = User.objects.filter(organization_id=organization_id)
        return [
            UserData(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role,
                organization_id=str(user.organization_id) if user.organization_id else None,
                is_active=user.is_active,
            )
            for user in users
        ]
    
    def validate_api_key(self, api_key: str) -> Optional[APIKeyData]:
        """Validate an API key using Django ORM."""
        from apps.api_keys.models import APIKey
        from django.utils import timezone
        
        try:
            # Use the secure lookup via HMAC
            key_hmac = APIKey._hmac(api_key)
            api_key_obj = APIKey.objects.get(
                key_hmac=key_hmac,
                status=APIKey.Status.ACTIVE,
            )
            
            # Check expiration
            if api_key_obj.expires_at and api_key_obj.expires_at < timezone.now():
                return APIKeyData(
                    id=str(api_key_obj.id),
                    organization_id=str(api_key_obj.organization_id),
                    scope=api_key_obj.scope,
                    is_valid=False,
                    rate_limit_per_minute=api_key_obj.rate_limit_per_minute,
                )
            
            # Check quota
            if api_key_obj.quota and api_key_obj.usage_count >= api_key_obj.quota:
                return APIKeyData(
                    id=str(api_key_obj.id),
                    organization_id=str(api_key_obj.organization_id),
                    scope=api_key_obj.scope,
                    is_valid=False,
                    rate_limit_per_minute=api_key_obj.rate_limit_per_minute,
                )
            
            return APIKeyData(
                id=str(api_key_obj.id),
                organization_id=str(api_key_obj.organization_id),
                scope=api_key_obj.scope,
                is_valid=True,
                rate_limit_per_minute=api_key_obj.rate_limit_per_minute,
            )
        except APIKey.DoesNotExist:
            logger.warning("Invalid API key attempted")
            return None


# Singleton instance - will be replaced with HTTP client in Phase 2
_identity_service: Optional[IdentityServiceInterface] = None


def get_identity_service() -> IdentityServiceInterface:
    """Get the Identity Service instance."""
    global _identity_service
    if _identity_service is None:
        _identity_service = LocalIdentityService()
    return _identity_service


def set_identity_service(service: IdentityServiceInterface) -> None:
    """Set a custom Identity Service instance (for testing or Phase 2)."""
    global _identity_service
    _identity_service = service
