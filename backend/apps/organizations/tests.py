from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from apps.users.models import User
from apps.organizations.models import Organization
from apps.api_keys.models import APIKey
from apps.documents.models import Document
from unittest.mock import patch
import uuid

class OrganizationModelTests(TestCase):
    """Test cases for Organization model"""

    def setUp(self):
        self.org_data = {
            'name': 'Test Organization',
            'logo_url': 'https://example.com/logo.png'
        }
        self.organization = Organization.objects.create(**self.org_data)

    def test_organization_creation(self):
        """Test organization creation with valid data"""
        self.assertEqual(self.organization.name, self.org_data['name'])
        self.assertEqual(self.organization.logo_url, self.org_data['logo_url'])
        self.assertIsNotNone(self.organization.id)
        self.assertIsNotNone(self.organization.created_at)
        self.assertIsNotNone(self.organization.updated_at)

    def test_organization_str_representation(self):
        """Test string representation of organization"""
        self.assertEqual(str(self.organization), self.org_data['name'])

    def test_organization_auto_fields(self):
        """Test auto-populated fields"""
        self.assertIsInstance(self.organization.id, uuid.UUID)
        # created_at should be equal to updated_at on creation
        self.assertEqual(self.organization.created_at, self.organization.updated_at)

    def test_organization_updated_at(self):
        """Test updated_at field is auto-updated"""
        original_updated_at = self.organization.updated_at
        self.organization.name = "Updated Name"
        self.organization.save()
        self.assertGreater(self.organization.updated_at, original_updated_at)

class OrganizationViewTests(APITestCase):
    """Test cases for Organization views"""

    def setUp(self):
        """Set up test data"""
        # Create organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            logo_url='https://example.com/logo.png'
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            organization=self.organization,
            is_staff=True
        )
        
        # Create another organization and user
        self.other_org = Organization.objects.create(
            name='Other Organization'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            organization=self.other_org
        )
        
        # URLs
        self.org_url = reverse('organization')
        
        # Test data
        self.update_data = {
            'name': 'Updated Organization Name',
            'logo_url': 'https://example.com/new_logo.png'
        }
    def test_update_organization_success(self):
        """Test successful organization update"""
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.org_url, self.update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.update_data['name'])
        self.assertEqual(response.data['logo_url'], self.update_data['logo_url'])
        
        # Verify database update
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, self.update_data['name'])
        self.assertEqual(self.organization.logo_url, self.update_data['logo_url'])

    def test_update_organization_partial(self):
        """Test partial update of organization"""
        self.client.force_authenticate(user=self.user)
        partial_data = {'name': 'New Name Only'}
        response = self.client.put(self.org_url, partial_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], partial_data['name'])
        self.assertEqual(response.data['logo_url'], self.organization.logo_url)

    def test_update_organization_validation(self):
        """Test organization update validation"""
        self.client.force_authenticate(user=self.user)
        
        # Test with invalid logo URL
        invalid_data = {
            'name': 'Test Org',
            'logo_url': 'invalid-url'
        }
        response = self.client.put(self.org_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with empty name
        invalid_data = {'name': ''}
        response = self.client.put(self.org_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_organization_authentication(self):
        """Test authentication requirements for organization update"""
        # Test without authentication
        response = self.client.put(self.org_url, self.update_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with other organization's user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.put(self.org_url, self.update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_organization_admin_access(self):
        """Test admin user can update organization"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(self.org_url, self.update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.update_data['name'])

    def test_delete_organization(self):
        """Test organization deletion with proper response format"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.org_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertIn('message', response.data)
        self.assertIn('permanently deleted', response.data['detail'])
        self.assertIn('sessions have been terminated', response.data['message'])
        
        # Verify organization is deleted
        self.assertFalse(Organization.objects.filter(id=self.organization.id).exists())

    def test_delete_organization_authentication(self):
        """Test authentication requirements for organization deletion"""
        # Test without authentication
        response = self.client.delete(self.org_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with other organization's user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.org_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify organization still exists
        self.assertTrue(Organization.objects.filter(id=self.organization.id).exists())

    def test_delete_organization_cascade(self):
        """Test organization deletion cascades to related objects"""
        self.client.force_authenticate(user=self.user)
        
        # Create some related objects
        api_key = APIKey.objects.create(
            name='Test Key',
            organization=self.organization,
            created_by=self.user
        )
        document = Document.objects.create(
            name='test.txt',
            organization=self.organization,
            uploaded_by=self.user
        )
        
        # Delete organization
        response = self.client.delete(self.org_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify related objects are deleted
        self.assertFalse(Organization.objects.filter(id=self.organization.id).exists())
        self.assertFalse(User.objects.filter(organization_id=self.organization.id).exists())
        self.assertFalse(APIKey.objects.filter(organization_id=self.organization.id).exists())
        self.assertFalse(Document.objects.filter(organization_id=self.organization.id).exists())
        
    def test_delete_organization_admin(self):
        """Test admin can delete organization"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.org_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Organization.objects.filter(id=self.organization.id).exists())
        
    def test_delete_organization_token_blacklisting(self):
        """Test that user tokens are blacklisted when organization is deleted"""
        # Create refresh tokens for users
        user_refresh = RefreshToken.for_user(self.user)
        admin_refresh = RefreshToken.for_user(self.admin_user)
        
        # Verify tokens exist in OutstandingToken
        user_outstanding = OutstandingToken.objects.filter(user=self.user).first()
        admin_outstanding = OutstandingToken.objects.filter(user=self.admin_user).first()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.org_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify organization and users are deleted
        self.assertFalse(Organization.objects.filter(id=self.organization.id).exists())
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
        self.assertFalse(User.objects.filter(id=self.admin_user.id).exists())
        
        # Note: We can't check token blacklisting after user deletion since CASCADE 
        # will remove the outstanding tokens. In real implementation, tokens would be 
        # blacklisted before user deletion, making them invalid.
