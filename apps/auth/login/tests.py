from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from django.test.utils import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class LoginViewTests(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        # Create an active user
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True
        )

    def test_successful_login(self):
        """Test successful login with valid credentials"""
        response = self.client.post(self.login_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify token works
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        # You could add an authenticated endpoint test here

    def test_login_with_invalid_password(self):
        """Test login with invalid password"""
        invalid_data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_with_inactive_user(self):
        """Test login with an inactive user account"""
        # Make user inactive
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.login_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_with_nonexistent_user(self):
        """Test login with email that doesn't exist"""
        nonexistent_data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, nonexistent_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_with_missing_fields(self):
        """Test login with missing required fields"""
        # Test missing email
        response = self.client.post(self.login_url, {'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test missing password
        response = self.client.post(self.login_url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_with_invalid_email_format(self):
        """Test login with invalid email format"""
        invalid_email_data = {
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, invalid_email_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_THROTTLE_RATES': {
            'login': '3/minute',
        }
    })
    def test_login_throttling(self):
        """Test login throttling"""
        # Make 3 requests (our limit)
        for _ in range(3):
            response = self.client.post(self.login_url, self.user_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The 4th request should be throttled
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_method_not_allowed(self):
        """Test that only POST method is allowed"""
        # Test GET method
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test PUT method
        response = self.client.put(self.login_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test DELETE method
        response = self.client.delete(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('rest_framework_simplejwt.tokens.RefreshToken.for_user')
    def test_token_generation_failure(self, mock_for_user):
        """Test handling of token generation failure"""
        mock_for_user.side_effect = Exception("Token generation failed")
        
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
