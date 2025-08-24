from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.organizations.models import Organization
from apps.api_keys.models import APIKey

class APIKeyModelTests(TestCase):
    """Test cases for APIKey model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name="Test Organization")
        self.api_key_data = {
            "organization": self.org,
            "name": "Test API Key",
            "quota": 1000,
            "scope": APIKey.Scope.FULL
        }
        self.api_key = APIKey.objects.create(**self.api_key_data)
        self.plaintext = APIKey.generate_plaintext()
        self.api_key.key = self.plaintext

    def test_api_key_creation(self):
        """Test API key creation with valid data"""
        self.assertEqual(self.api_key.name, self.api_key_data["name"])
        self.assertEqual(self.api_key.quota, self.api_key_data["quota"])
        self.assertEqual(self.api_key.scope, self.api_key_data["scope"])
        self.assertEqual(self.api_key.organization, self.org)
        self.assertEqual(self.api_key.status, APIKey.Status.ACTIVE)
        self.assertEqual(self.api_key.usage_count, 0)
        self.assertIsNotNone(self.api_key.id)
        self.assertIsNotNone(self.api_key.created_at)

    def test_api_key_encryption(self):
        """Test API key encryption and retrieval"""
        plaintext = APIKey.generate_plaintext()
        self.api_key.key = plaintext
        
        # Key should be encrypted in database
        self.assertNotEqual(self.api_key.key_encrypted, plaintext)
        
        # But retrievable through the property
        self.assertEqual(self.api_key.key, plaintext)

    def test_api_key_hmac(self):
        """Test API key HMAC generation and lookup"""
        plaintext = APIKey.generate_plaintext()
        self.api_key.key = plaintext
        
        # HMAC should be set
        self.assertIsNotNone(self.api_key.key_hmac)
        
        # Should be able to lookup by plaintext
        found_key = APIKey.get_by_plaintext(plaintext)
        self.assertEqual(found_key.id, self.api_key.id)

    def test_api_key_scopes(self):
        """Test API key scopes"""
        scopes = [
            APIKey.Scope.FULL,
            APIKey.Scope.READ_ONLY,
            APIKey.Scope.UPLOAD_ONLY
        ]
        
        for scope in scopes:
            api_key = APIKey.objects.create(
                organization=self.org,
                name=f"Test Key {scope}",
                scope=scope
            )
            self.assertEqual(api_key.scope, scope)

    def test_api_key_status_change(self):
        """Test API key status changes"""
        self.assertEqual(self.api_key.status, APIKey.Status.ACTIVE)
        
        self.api_key.status = APIKey.Status.REVOKED
        self.api_key.save()
        self.api_key.refresh_from_db()
        
        self.assertEqual(self.api_key.status, APIKey.Status.REVOKED)

    def test_api_key_usage_count(self):
        """Test API key usage counting"""
        initial_count = self.api_key.usage_count
        self.api_key.usage_count += 1
        self.api_key.save()
        self.api_key.refresh_from_db()
        
        self.assertEqual(self.api_key.usage_count, initial_count + 1)

class APIKeyViewTests(APITestCase):
    """Test cases for API key views"""

    def setUp(self):
        """Set up test data"""
        # Create organization
        self.org = Organization.objects.create(name="Test Organization")
        
        # Create users
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            role=User.Role.MEMBER
        )
        
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            organization=self.org,
            role=User.Role.ADMIN,
            is_staff=True
        )
        
        # Create another organization and user
        self.other_org = Organization.objects.create(name="Other Organization")
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
            organization=self.other_org
        )
        
        # Create API key
        self.api_key = APIKey.objects.create(
            organization=self.org,
            name="Test API Key",
            quota=1000,
            scope=APIKey.Scope.FULL
        )
        self.plaintext = APIKey.generate_plaintext()
        self.api_key.key = self.plaintext
        self.api_key.save()
        
        # URLs
        self.list_create_url = reverse("api-keys-list")
        self.revoke_url = reverse("api-key-revoke", kwargs={"pk": self.api_key.id})
        self.delete_url = reverse("api-key-delete", kwargs={"pk": self.api_key.id})
        
        # Test data
        self.create_data = {
            "name": "New API Key",
            "quota": 500,
            "scope": APIKey.Scope.READ_ONLY
        }
        
        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_list_api_keys(self):
        """Test listing API keys"""
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.api_key.name)

    def test_create_api_key_validation(self):
        """Test API key creation validation"""
        # Test with invalid scope
        invalid_data = {**self.create_data, "scope": "invalid"}
        response = self.client.post(self.list_create_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with negative quota
        invalid_data = {**self.create_data, "quota": -1}
        response = self.client.post(self.list_create_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with empty name
        invalid_data = {**self.create_data, "name": ""}
        response = self.client.post(self.list_create_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revoke_api_key(self):
        """Test revoking an API key"""
        response = self.client.patch(self.revoke_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify key is revoked
        self.api_key.refresh_from_db()
        self.assertEqual(self.api_key.status, APIKey.Status.REVOKED)

    def test_delete_api_key(self):
        """Test deleting an API key"""
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(APIKey.objects.filter(id=self.api_key.id).exists())

    def test_api_key_permissions(self):
        """Test API key permissions"""
        # Test with other organization's user
        self.client.force_authenticate(user=self.other_user)
        
        # Should not see the key
        response = self.client.get(self.list_create_url)
        self.assertEqual(len(response.data), 0)
        
        # Should not be able to revoke
        response = self.client.patch(self.revoke_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should not be able to delete
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_key_admin_access(self):
        """Test admin access to API keys"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Admin should see all keys
        response = self.client.get(self.list_create_url)
        self.assertEqual(len(response.data), 1)
        
        # Admin should be able to create
        response = self.client.post(self.list_create_url, self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Admin should be able to revoke
        response = self.client.patch(self.revoke_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Admin should be able to delete
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_api_key_unauthenticated(self):
        """Test unauthenticated access to API keys"""
        self.client.force_authenticate(user=None)
        
        # Should not be able to list
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Should not be able to create
        response = self.client.post(self.list_create_url, self.create_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Should not be able to revoke
        response = self.client.patch(self.revoke_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Should not be able to delete
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_api_key(self):
        """Test creating a new API key"""
        url = reverse('api-key-list')
        data = {'name': 'New Test Key'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Test Key')
        self.assertIn('key', response.data)

    def test_unauthorized_access(self):
        """Test unauthorized access to API keys"""
        self.client.credentials()  # Remove authentication
        url = reverse('api-key-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test accessing API keys from wrong organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_key = APIKey.objects.create(
            name='Other Key',
            organization=other_org
        )
        url = reverse('api-key-delete', kwargs={'pk': other_key.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
