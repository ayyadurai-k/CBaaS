from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from apps.chatbot_provider.models import ChatbotProvider
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

class ChatbotProviderTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
        
        # Create test provider
        self.provider = ChatbotProvider.objects.create(
            name='Test Provider',
            provider_type='openai',
            api_key='test-key',
            organization=self.organization,
            settings={
                'model': 'gpt-4',
                'base_url': 'https://api.openai.com/v1'
            }
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_test_key(self):
        """Test provider key validation"""
        url = reverse('provider-test-key')
        data = {
            'provider_type': 'openai',
            'api_key': 'test-key',
            'settings': {
                'model': 'gpt-4',
                'base_url': 'https://api.openai.com/v1'
            }
        }
        
        # Mock the API client test call
        with patch('apps.chatbot_provider.views.test_provider_key') as mock_test:
            mock_test.return_value = True
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['valid'])

    def test_invalid_key(self):
        """Test invalid provider key"""
        url = reverse('provider-test-key')
        data = {
            'provider_type': 'openai',
            'api_key': 'invalid-key',
            'settings': {
                'model': 'gpt-4'
            }
        }
        
        # Mock the API client test call
        with patch('apps.chatbot_provider.views.test_provider_key') as mock_test:
            mock_test.return_value = False
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data['valid'])

    def test_upsert_provider(self):
        """Test creating/updating provider"""
        url = reverse('provider-upsert')
        data = {
            'name': 'Updated Provider',
            'provider_type': 'openai',
            'api_key': 'new-test-key',
            'settings': {
                'model': 'gpt-4',
                'temperature': 0.7
            }
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.name, 'Updated Provider')
        self.assertEqual(self.provider.settings['temperature'], 0.7)

    def test_invalid_provider_type(self):
        """Test creating provider with invalid type"""
        url = reverse('provider-upsert')
        data = {
            'name': 'Invalid Provider',
            'provider_type': 'invalid-type',
            'api_key': 'test-key'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        """Test unauthorized access to provider endpoints"""
        self.client.credentials()  # Remove authentication
        url = reverse('provider-upsert')
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test accessing provider from wrong organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            organization=other_org
        )
        
        # Login as other user
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('provider-upsert')
        data = {
            'name': 'Hacked Provider',
            'provider_type': 'openai',
            'api_key': 'hacked-key'
        }
        response = self.client.put(url, data, format='json')
        
        # Should create new provider for other org, not modify existing
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.name, 'Test Provider')
