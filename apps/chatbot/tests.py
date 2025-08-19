from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from apps.chatbot.models import Chatbot
from rest_framework_simplejwt.tokens import RefreshToken

class ChatbotTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
        
        # Create test chatbot
        self.chatbot = Chatbot.objects.create(
            name='Test Bot',
            description='A test chatbot',
            organization=self.organization,
            settings={
                'temperature': 0.7,
                'max_tokens': 1000
            }
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_chatbot(self):
        """Test retrieving chatbot details"""
        url = reverse('chatbot-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Bot')
        self.assertEqual(response.data['description'], 'A test chatbot')
        self.assertEqual(response.data['settings']['temperature'], 0.7)

    def test_update_chatbot(self):
        """Test updating chatbot settings"""
        url = reverse('chatbot-detail')
        data = {
            'name': 'Updated Bot',
            'description': 'Updated description',
            'settings': {
                'temperature': 0.8,
                'max_tokens': 2000
            }
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chatbot.refresh_from_db()
        self.assertEqual(self.chatbot.name, 'Updated Bot')
        self.assertEqual(self.chatbot.settings['temperature'], 0.8)

    def test_invalid_settings(self):
        """Test updating chatbot with invalid settings"""
        url = reverse('chatbot-detail')
        data = {
            'name': 'Updated Bot',
            'settings': {
                'temperature': 2.0  # Invalid temperature value
            }
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        """Test unauthorized access to chatbot"""
        self.client.credentials()  # Remove authentication
        url = reverse('chatbot-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test accessing chatbot from wrong organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            organization=other_org
        )
        
        # Login as other user
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('chatbot-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
