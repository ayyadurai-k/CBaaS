from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Test Org')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'organization': self.organization
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_signup(self):
        """Test user signup"""
        url = reverse('auth-signup')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'organization_name': 'New Org'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login(self):
        """Test user login"""
        url = reverse('auth-login')
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_logout(self):
        """Test user logout"""
        # First login to get token
        login_url = reverse('auth-login')
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        login_response = self.client.post(login_url, login_data)
        token = login_response.data['access']

        # Then logout
        logout_url = reverse('auth-logout')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_flow(self):
        """Test complete password reset flow"""
        # 1. Request password reset
        forgot_url = reverse('auth-forgot-password')
        response = self.client.post(forgot_url, {'email': self.user_data['email']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Verify reset token (simulated)
        self.user.refresh_from_db()
        verify_url = reverse('auth-verify-reset-token')
        response = self.client.post(verify_url, {
            'email': self.user_data['email'],
            'token': 'simulated-token'  # In real tests, get actual token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Reset password
        reset_url = reverse('auth-reset-password')
        response = self.client.post(reset_url, {
            'email': self.user_data['email'],
            'token': 'simulated-token',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        url = reverse('auth-login')
        data = {
            'email': self.user_data['email'],
            'password': 'wrongpass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_logout(self):
        """Test logout with invalid token"""
        url = reverse('auth-logout')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
