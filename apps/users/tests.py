from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from rest_framework_simplejwt.tokens import RefreshToken

class UserTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization,
            first_name='Test',
            last_name='User'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_profile(self):
        """Test getting user profile"""
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['organization']['name'], 'Test Org')

    def test_unauthorized_access(self):
        """Test unauthorized access to profile"""
        self.client.credentials()  # Remove authentication
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_token(self):
        """Test accessing profile with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
