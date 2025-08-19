from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.api_keys.models import APIKey
from apps.users.models import User
from apps.organizations.models import Organization
from rest_framework_simplejwt.tokens import RefreshToken

class APIKeyTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org'
        )
        self.user.organization = self.organization
        self.user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test API key
        self.api_key = APIKey.objects.create(
            name='Test Key',
            organization=self.organization
        )

    def test_list_api_keys(self):
        """Test listing API keys"""
        url = reverse('api-key-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Key')

    def test_create_api_key(self):
        """Test creating a new API key"""
        url = reverse('api-key-list')
        data = {'name': 'New Test Key'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Test Key')
        self.assertIn('key', response.data)

    def test_revoke_api_key(self):
        """Test revoking an API key"""
        url = reverse('api-key-revoke', kwargs={'pk': self.api_key.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.api_key.refresh_from_db()
        self.assertTrue(self.api_key.revoked)

    def test_delete_api_key(self):
        """Test deleting an API key"""
        url = reverse('api-key-delete', kwargs={'pk': self.api_key.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(APIKey.objects.count(), 0)

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
