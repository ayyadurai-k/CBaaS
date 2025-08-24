from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.test.utils import override_settings
from rest_framework_simplejwt.tokens import RefreshToken
from apps.organizations.models import Organization
from apps.users.models import User
from django.utils import timezone
from datetime import timedelta
import jwt
from django.conf import settings

class BaseAuthTestCase(APITestCase):
    def setUp(self):
        """Set up test data common to all auth tests"""
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Test Org",
            slug="test-org"
        )
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'organization': self.organization
        }
        self.user = User.objects.create_user(**self.user_data)
        self.user.is_active = True
        self.user.save()

class LoginViewTests(BaseAuthTestCase):
    def setUp(self):
        """Set up test data specific to login tests"""
        super().setUp()
        self.login_url = reverse('login')
        self.login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }

    def test_successful_login(self):
        """Test successful login with valid credentials"""
        response = self.client.post(self.login_url, self.login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify token payload
        access_token = response.data['access']
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(payload['user_id'], self.user.id)
        self.assertIn('exp', payload)
        self.assertIn('iat', payload)

    def test_login_with_invalid_password(self):
        """Test login with invalid password"""
        invalid_data = {**self.login_data, 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_with_inactive_user(self):
        """Test login with an inactive user account"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.login_url, self.login_data)
        
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

        # Test empty payload
        response = self.client.post(self.login_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
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
            response = self.client.post(self.login_url, self.login_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The 4th request should be throttled
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_method_not_allowed(self):
        """Test that only POST method is allowed"""
        # Test GET method
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test PUT method
        response = self.client.put(self.login_url, self.login_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test DELETE method
        response = self.client.delete(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('rest_framework_simplejwt.tokens.RefreshToken.for_user')
    def test_token_generation_failure(self, mock_for_user):
        """Test handling of token generation failure"""
        mock_for_user.side_effect = Exception("Token generation failed")
        
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_login_with_uppercase_email(self):
        """Test login with uppercase email address"""
        uppercase_data = {
            'email': self.login_data['email'].upper(),
            'password': self.login_data['password']
        }
        response = self.client.post(self.login_url, uppercase_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_concurrent_login_sessions(self):
        """Test multiple concurrent login sessions"""
        # First login
        response1 = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second login
        response2 = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify both tokens are different
        self.assertNotEqual(response1.data['access'], response2.data['access'])
        self.assertNotEqual(response1.data['refresh'], response2.data['refresh'])

class LogoutViewTests(BaseAuthTestCase):
    def setUp(self):
        """Set up test data specific to logout tests"""
        super().setUp()
        self.logout_url = reverse('logout')
        # Login and get tokens
        response = self.client.post(reverse('login'), {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_successful_logout(self):
        """Test successful logout with valid refresh token"""
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_logout_without_refresh_token(self):
        """Test logout without providing refresh token"""
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_refresh_token(self):
        """Test logout with invalid refresh token"""
        response = self.client.post(self.logout_url, {'refresh': 'invalid-token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_authentication(self):
        """Test logout without authentication header"""
        self.client.credentials()  # Remove authentication
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_method_not_allowed(self):
        """Test that only POST method is allowed for logout"""
        # Test GET method
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test PUT method
        response = self.client.put(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_reuse_token_after_logout(self):
        """Test that tokens can't be reused after logout"""
        # First logout
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Try to use the same refresh token
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SignupViewTests(BaseAuthTestCase):
    def setUp(self):
        """Set up test data specific to signup tests"""
        super().setUp()
        self.signup_url = reverse('signup')
        self.signup_data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'organization': {
                'name': 'New Org',
                'slug': 'new-org'
            }
        }

    def test_successful_signup(self):
        """Test successful user signup"""
        response = self.client.post(self.signup_url, self.signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify user creation
        user = User.objects.get(email=self.signup_data['email'])
        self.assertEqual(user.first_name, self.signup_data['first_name'])
        self.assertEqual(user.last_name, self.signup_data['last_name'])
        self.assertTrue(user.is_active)

        # Verify organization creation
        org = Organization.objects.get(slug=self.signup_data['organization']['slug'])
        self.assertEqual(org.name, self.signup_data['organization']['name'])

    def test_signup_with_existing_email(self):
        """Test signup with already registered email"""
        existing_data = {**self.signup_data, 'email': self.user_data['email']}
        response = self.client.post(self.signup_url, existing_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_signup_with_existing_org_slug(self):
        """Test signup with already existing organization slug"""
        existing_org_data = {
            **self.signup_data,
            'organization': {
                'name': 'Another Org',
                'slug': self.organization.slug
            }
        }
        response = self.client.post(self.signup_url, existing_org_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('organization', response.data)

    def test_signup_with_invalid_data(self):
        """Test signup with invalid data"""
        # Test invalid email
        invalid_email_data = {**self.signup_data, 'email': 'invalid-email'}
        response = self.client.post(self.signup_url, invalid_email_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test weak password
        weak_password_data = {**self.signup_data, 'password': '123'}
        response = self.client.post(self.signup_url, weak_password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        # Test invalid organization slug
        invalid_slug_data = {
            **self.signup_data,
            'organization': {
                'name': 'Test Org',
                'slug': 'invalid slug with spaces'
            }
        }
        response = self.client.post(self.signup_url, invalid_slug_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('organization', response.data)

    def test_signup_with_missing_fields(self):
        """Test signup with missing required fields"""
        required_fields = ['email', 'password', 'first_name', 'last_name', 'organization']
        
        for field in required_fields:
            data = self.signup_data.copy()
            if field == 'organization':
                del data[field]
            else:
                data[field] = ''
            
            response = self.client.post(self.signup_url, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, str(response.data))

    @patch('apps.auth.signup.views.SignupView.post')
    def test_signup_internal_error(self, mock_post):
        """Test handling of internal server error during signup"""
        mock_post.side_effect = Exception("Internal error")
        response = self.client.post(self.signup_url, self.signup_data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_signup_method_not_allowed(self):
        """Test that only POST method is allowed for signup"""
        # Test GET method
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test PUT method
        response = self.client.put(self.signup_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class ResetPasswordViewTests(BaseAuthTestCase):
    def setUp(self):
        """Set up test data specific to password reset tests"""
        super().setUp()
        self.forgot_url = reverse('forgot-password')
        self.verify_url = reverse('verify-reset-token')
        self.reset_url = reverse('reset-password')

    def test_forgot_password_success(self):
        """Test successful password reset request"""
        response = self.client.post(self.forgot_url, {'email': self.user_data['email']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_nonexistent_email(self):
        """Test password reset request for non-existent email"""
        response = self.client.post(self.forgot_url, {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_verify_reset_token_success(self):
        """Test successful verification of reset token"""
        # First request password reset
        self.client.post(self.forgot_url, {'email': self.user_data['email']})
        # Get the token (in real scenario this would be sent via email)
        user = User.objects.get(email=self.user_data['email'])
        token = user.reset_token
        
        response = self.client.post(self.verify_url, {'token': token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_reset_token_invalid(self):
        """Test verification with invalid reset token"""
        response = self.client.post(self.verify_url, {'token': 'invalid-token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_reset_token_expired(self):
        """Test verification with expired reset token"""
        # First request password reset
        self.client.post(self.forgot_url, {'email': self.user_data['email']})
        user = User.objects.get(email=self.user_data['email'])
        
        # Expire the token
        user.reset_token_expiry = timezone.now() - timedelta(hours=1)
        user.save()
        
        response = self.client.post(self.verify_url, {'token': user.reset_token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_success(self):
        """Test successful password reset"""
        # First request password reset
        self.client.post(self.forgot_url, {'email': self.user_data['email']})
        user = User.objects.get(email=self.user_data['email'])
        token = user.reset_token
        
        new_password = 'newpassword123'
        response = self.client.post(self.reset_url, {
            'token': token,
            'password': new_password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify can login with new password
        login_response = self.client.post(reverse('login'), {
            'email': self.user_data['email'],
            'password': new_password
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token"""
        response = self.client.post(self.reset_url, {
            'token': 'invalid-token',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_weak_password(self):
        """Test password reset with weak password"""
        # First request password reset
        self.client.post(self.forgot_url, {'email': self.user_data['email']})
        user = User.objects.get(email=self.user_data['email'])
        token = user.reset_token
        
        response = self.client.post(self.reset_url, {
            'token': token,
            'password': '123'  # weak password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
