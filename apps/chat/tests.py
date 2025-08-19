from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from apps.chatbot_provider.models import ChatbotProvider
from rest_framework_simplejwt.tokens import RefreshToken
import json

class ChatTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
        
        # Create test chatbot provider
        self.provider = ChatbotProvider.objects.create(
            name='Test Provider',
            provider_type='openai',
            api_key='test-key',
            organization=self.organization
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_chat_completion(self):
        """Test chat completion endpoint"""
        url = reverse('chat-completion')
        data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'provider_id': self.provider.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('choices', response.data)

    def test_chat_stream(self):
        """Test chat streaming endpoint"""
        url = reverse('chat-stream')
        data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'provider_id': self.provider.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response is streaming
        self.assertEqual(response.get('Content-Type'), 'text/event-stream')

    def test_invalid_provider(self):
        """Test chat with invalid provider"""
        url = reverse('chat-completion')
        data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'provider_id': 999  # Invalid ID
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_messages(self):
        """Test chat with empty messages"""
        url = reverse('chat-completion')
        data = {
            'messages': [],
            'provider_id': self.provider.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        """Test unauthorized access to chat endpoints"""
        self.client.credentials()  # Remove authentication
        url = reverse('chat-completion')
        data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'provider_id': self.provider.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
