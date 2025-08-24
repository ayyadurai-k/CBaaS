from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.organizations.models import Organization
from apps.chatbot.models import Chatbot
import uuid
from rest_framework_simplejwt.tokens import RefreshToken


class ChatbotModelTests(TestCase):
    """Test cases for Chatbot model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name="Test Organization")
        self.chatbot_data = {
            "organization": self.org,
            "name": "Test Chatbot",
            "tone": "Technical",
            "system_instructions": "You are a helpful AI assistant.",
        }
        self.chatbot = Chatbot.objects.create(**self.chatbot_data)

    def test_chatbot_creation(self):
        """Test chatbot creation with valid data"""
        self.assertEqual(self.chatbot.name, self.chatbot_data["name"])
        self.assertEqual(self.chatbot.tone, self.chatbot_data["tone"])
        self.assertEqual(
            self.chatbot.system_instructions, self.chatbot_data["system_instructions"]
        )
        self.assertEqual(self.chatbot.organization, self.org)
        self.assertIsNotNone(self.chatbot.id)
        self.assertIsNotNone(self.chatbot.created_at)
        self.assertIsNotNone(self.chatbot.updated_at)

    def test_chatbot_str_representation(self):
        """Test string representation of chatbot"""
        self.assertEqual(str(self.chatbot), self.chatbot.name)

    def test_chatbot_auto_fields(self):
        """Test auto-populated fields"""
        self.assertIsInstance(self.chatbot.id, uuid.UUID)
        self.assertEqual(self.chatbot.created_at, self.chatbot.updated_at)

    def test_chatbot_updated_at(self):
        """Test updated_at field is auto-updated"""
        original_updated_at = self.chatbot.updated_at
        self.chatbot.name = "Updated Name"
        self.chatbot.save()
        self.assertGreater(self.chatbot.updated_at, original_updated_at)

    def test_chatbot_tone_choices(self):
        """Test chatbot tone choices"""
        valid_tones = ["Friendly", "Technical", "Formal"]
        for tone in valid_tones:
            chatbot = Chatbot.objects.create(
                organization=self.org, name=f"{tone} Bot", tone=tone
            )
            self.assertEqual(chatbot.tone, tone)

    def test_chatbot_defaults(self):
        """Test chatbot default values"""
        minimal_bot = Chatbot.objects.create(organization=self.org, name="Minimal Bot")
        self.assertEqual(minimal_bot.tone, "Technical")  # Default tone
        self.assertEqual(minimal_bot.system_instructions, "")  # Empty string default


class ChatbotViewTests(APITestCase):
    """Test cases for ChatbotView"""

    def setUp(self):
        """Set up test data"""
        # Create organization
        self.org = Organization.objects.create(name="Test Organization")

        # Create another organization
        self.other_org = Organization.objects.create(name="Other Organization")

        # Create users
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            role=User.Role.MEMBER,
        )

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            organization=self.org,
            role=User.Role.ADMIN,
            is_staff=True,
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
            organization=self.other_org,
        )

        # Create test chatbot
        self.chatbot = Chatbot.objects.create(
            organization=self.org,
            name="Test Chatbot",
            tone="Technical",
            system_instructions="Test instructions",
        )

        # Set up URL and authenticate
        self.url = reverse("chatbot")
        self.client.force_authenticate(user=self.user)

        # Test data for updates
        self.update_data = {
            "name": "Updated Chatbot",
            "tone": "Friendly",
            "system_instructions": "Updated instructions",
        }

    def test_get_chatbot_success(self):
        """Test successful retrieval of chatbot"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.chatbot.name)
        self.assertEqual(response.data["tone"], self.chatbot.tone)
        self.assertEqual(
            response.data["system_instructions"], self.chatbot.system_instructions
        )

    def test_get_chatbot_auto_create(self):
        """Test auto-creation of chatbot if it doesn't exist"""
        # Delete existing chatbot
        self.chatbot.delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], f"{self.org.name} Chatbot")
        self.assertEqual(response.data["tone"], "Technical")
        self.assertEqual(response.data["system_instructions"], "")

    def test_update_chatbot_success(self):
        """Test successful update of chatbot"""
        response = self.client.put(self.url, self.update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.update_data["name"])
        self.assertEqual(response.data["tone"], self.update_data["tone"])
        self.assertEqual(
            response.data["system_instructions"],
            self.update_data["system_instructions"],
        )

        # Verify database update
        self.chatbot.refresh_from_db()
        self.assertEqual(self.chatbot.name, self.update_data["name"])

    def test_update_chatbot_partial(self):
        """Test partial update of chatbot"""
        partial_data = {"name": "New Name Only"}
        response = self.client.put(self.url, partial_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], partial_data["name"])
        # Other fields should remain unchanged
        self.assertEqual(response.data["tone"], self.chatbot.tone)
        self.assertEqual(
            response.data["system_instructions"], self.chatbot.system_instructions
        )

    def test_update_chatbot_validation(self):
        """Test chatbot update validation"""
        # Test with invalid tone
        invalid_data = {"name": "Test Bot", "tone": "Invalid"}
        response = self.client.put(self.url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test with empty name
        invalid_data = {"name": ""}
        response = self.client.put(self.url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chatbot_authentication(self):
        """Test authentication requirements"""
        # Test without authentication
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with wrong organization's user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        # Should create a new chatbot for other_user's organization
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data["id"], str(self.chatbot.id))

    def test_chatbot_admin_access(self):
        """Test admin user access"""
        self.client.force_authenticate(user=self.admin_user)

        # Admin should be able to view and update
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.url, self.update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_chatbot(self):
        """Test retrieving chatbot details"""
        url = reverse("chatbot-detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Bot")
        self.assertEqual(response.data["description"], "A test chatbot")

    def test_update_chatbot(self):
        """Test updating chatbot settings"""
        url = reverse("chatbot-detail")
        data = {
            "name": "Updated Bot",
            "description": "Updated description",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chatbot.refresh_from_db()
        self.assertEqual(self.chatbot.name, "Updated Bot")

    def test_unauthorized_access(self):
        """Test unauthorized access to chatbot"""
        self.client.credentials()  # Remove authentication
        url = reverse("chatbot-detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test accessing chatbot from wrong organization"""
        other_org = Organization.objects.create(name="Other Org")
        other_user = User.objects.create_user(
            email="other@example.com", password="testpass123", organization=other_org
        )

        # Login as other user
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        url = reverse("chatbot-detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
