from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.organizations.models import Organization
import uuid

class UserModelTests(TestCase):
    """Test cases for User model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name="Test Organization")
        self.user_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User",
            "organization": self.org,
            "role": User.Role.MEMBER
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Test user creation with valid data"""
        self.assertEqual(self.user.email, self.user_data["email"])
        self.assertTrue(self.user.check_password(self.user_data["password"]))
        self.assertEqual(self.user.name, self.user_data["name"])
        self.assertEqual(self.user.organization, self.org)
        self.assertEqual(self.user.role, User.Role.MEMBER)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertIsNotNone(self.user.id)
        self.assertIsNotNone(self.user.created_at)
        self.assertIsNotNone(self.user.updated_at)

    def test_create_superuser(self):
        """Test superuser creation"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            name="Admin User"
        )
        self.assertEqual(superuser.role, User.Role.OWNER)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_manager_validations(self):
        """Test UserManager validations"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="testpass123")

    def test_user_roles(self):
        """Test user role assignments and choices"""
        # Test OWNER role
        owner = User.objects.create_user(
            email="owner@example.com",
            password="pass123",
            role=User.Role.OWNER
        )
        self.assertEqual(owner.role, User.Role.OWNER)

        # Test ADMIN role
        admin = User.objects.create_user(
            email="admin@example.com",
            password="pass123",
            role=User.Role.ADMIN
        )
        self.assertEqual(admin.role, User.Role.ADMIN)

        # Test default MEMBER role
        member = User.objects.create_user(
            email="member@example.com",
            password="pass123"
        )
        self.assertEqual(member.role, User.Role.MEMBER)

    def test_user_auto_fields(self):
        """Test auto-populated fields"""
        self.assertIsInstance(self.user.id, uuid.UUID)
        self.assertEqual(self.user.created_at, self.user.updated_at)

    def test_user_updated_at(self):
        """Test updated_at field is auto-updated"""
        original_updated_at = self.user.updated_at
        self.user.name = "Updated Name"
        self.user.save()
        self.assertGreater(self.user.updated_at, original_updated_at)

    def test_user_unique_email(self):
        """Test email uniqueness constraint"""
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError
            User.objects.create_user(
                email=self.user_data["email"],  # Same email as existing user
                password="different123",
                name="Another User"
            )

class ProfileViewTests(APITestCase):
    """Test cases for ProfileView"""

    def setUp(self):
        """Set up test data"""
        # Create organization
        self.org = Organization.objects.create(
            name="Test Organization",
            logo_url="https://example.com/logo.png"
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            organization=self.org,
            role=User.Role.MEMBER
        )

        # Create admin user in same org
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            name="Admin User",
            organization=self.org,
            role=User.Role.ADMIN,
            is_staff=True
        )
        
        # Create another organization and user
        self.other_org = Organization.objects.create(
            name="Other Organization"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
            name="Other User",
            organization=self.other_org
        )
        
        # Set up URL and authenticate
        self.url = reverse("profile")
        self.client.force_authenticate(user=self.user)

    def test_get_profile_success(self):
        """Test successful retrieval of user profile"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user.id))
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["name"], self.user.name)
        self.assertEqual(response.data["role"], self.user.role)
        
        # Check organization data
        org_data = response.data["organization"]
        self.assertEqual(org_data["id"], str(self.org.id))
        self.assertEqual(org_data["name"], self.org.name)
        self.assertEqual(org_data["logo_url"], self.org.logo_url)
        self.assertIsNotNone(org_data["created_at"])
        self.assertIsNotNone(org_data["updated_at"])

    def test_get_profile_unauthenticated(self):
        """Test unauthenticated access to profile endpoint"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_no_organization(self):
        """Test profile retrieval for user without organization"""
        self.user.organization = None
        self.user.save()
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["organization"])

    def test_profile_data_structure(self):
        """Test the complete structure of profile response"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = {
            "id",
            "email",
            "name",
            "role",
            "created_at",
            "updated_at",
            "organization"
        }
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_profile_invalid_token(self):
        """Test accessing profile with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_expired_token(self):
        """Test accessing profile with expired token"""
        # Simulate expired token
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + "e" * 64)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
