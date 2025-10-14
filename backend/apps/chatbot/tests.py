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
        expected = f"{self.chatbot.name} ({self.chatbot.organization.name})"
        self.assertEqual(str(self.chatbot), expected)

    def test_chatbot_auto_fields(self):
        """Test auto-populated fields"""
        self.assertIsInstance(self.chatbot.id, uuid.UUID)
        # Check times are close (within 1 second) due to auto_now_add
        time_diff = abs((self.chatbot.created_at - self.chatbot.updated_at).total_seconds())
        self.assertLess(time_diff, 1)

    def test_chatbot_updated_at(self):
        """Test updated_at field is auto-updated"""
        original_updated_at = self.chatbot.updated_at
        self.chatbot.name = "Updated Name"
        self.chatbot.save()
        self.assertGreater(self.chatbot.updated_at, original_updated_at)

    def test_chatbot_tone_choices(self):
        """Test chatbot tone choices"""
        valid_tones = ["friendly", "technical", "formal", "professional"]
        for i, tone in enumerate(valid_tones):
            # Create separate org for each chatbot (unique constraint)
            org = Organization.objects.create(name=f"Test Org {i}")
            chatbot = Chatbot.objects.create(
                organization=org, name=f"{tone} Bot", tone=tone
            )
            self.assertEqual(chatbot.tone, tone)

    def test_chatbot_defaults(self):
        """Test chatbot default values"""
        # Create new org for second chatbot (unique constraint)
        new_org = Organization.objects.create(name="Test Organization 2")
        minimal_bot = Chatbot.objects.create(organization=new_org, name="Minimal Bot")
        self.assertEqual(minimal_bot.tone, "technical")  # Default tone
        self.assertEqual(minimal_bot.system_instructions, "")  # Empty string default


class ChatbotViewTests(APITestCase):
    """Test cases for ChatbotView"""

    def setUp(self):
        """Set up test data"""
        # Create organization
        self.org = Organization.objects.create(name="Test Organization")

        # Create another organization
        self.other_org = Organization.objects.create(name="Other Organization")

        # Create users (use ADMIN role for permissions)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            role=User.Role.ADMIN,
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
        self.url = reverse("chatbot-config")
        self.client.force_authenticate(user=self.user)

        # Test data for updates (tone must be lowercase)
        self.update_data = {
            "name": "Updated Chatbot",
            "tone": "friendly",
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
        self.assertEqual(response.data["tone"], "technical")
        self.assertEqual(response.data["system_instructions"], "")

    def test_update_chatbot_success(self):
        """Test successful update of chatbot"""
        response = self.client.put(self.url, self.update_data, format='json')

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
        response = self.client.put(self.url, partial_data, format='json')

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
        response = self.client.put(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test with empty name
        invalid_data = {"name": ""}
        response = self.client.put(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chatbot_authentication(self):
        """Test authentication requirements"""
        # Test without authentication
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with non-admin user (MEMBER role) - should be forbidden
        member_user = User.objects.create_user(
            email="member@example.com",
            password="testpass123",
            organization=self.org,
            role=User.Role.MEMBER,
        )
        self.client.force_authenticate(user=member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chatbot_admin_access(self):
        """Test admin user access"""
        self.client.force_authenticate(user=self.admin_user)

        # Admin should be able to view and update
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.url, self.update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChatbotMessageViewTests(APITestCase):
    """Test cases for ChatbotMessageView (RAG endpoint)"""

    def setUp(self):
        """Set up test data"""
        from unittest.mock import patch
        
        # Create organization
        self.org = Organization.objects.create(name="Test Organization", slug="test-org")

        # Create user with ADMIN role for permissions
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            is_active=True,
            role=User.Role.ADMIN,
        )

        # Create chatbot with LLM configured
        self.chatbot = Chatbot.objects.create(
            organization=self.org,
            name="Test Chatbot",
            tone="technical",
            system_instructions="You are a helpful assistant.",
            llm_provider="openai",
            llm_model="gpt-4",
            llm_is_active=True,
        )
        # Set encrypted API key
        self.chatbot.llm_api_key = "test-api-key"
        self.chatbot.save()

        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # URL and test data
        self.url = reverse("chatbot-message")
        self.message_data = {
            "message": "What is the meaning of life?",
            "history": []
        }

        # Mock RAG response (use real UUID format for document_id)
        import uuid as uuid_lib
        self.mock_doc_uuid = uuid_lib.uuid4()
        
        self.mock_rag_response = {
            "id": "resp_123",
            "session_id": None,
            "model": "gpt-4",
            "answer": "According to the documents, the meaning of life is 42.",
            "citations": [
                {
                    "document_id": str(self.mock_doc_uuid),
                    "chunk_index": 0,
                    "content": "The answer is 42",
                    "score": 0.95
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 15,
                "total_tokens": 35,
            },
            "latency_ms": 200,
        }

    def test_successful_message(self):
        """Test successful message with RAG"""
        from unittest.mock import patch
        
        with patch("apps.chatbot.views.chat_completion") as mock_chat:
            mock_chat.return_value = self.mock_rag_response
            
            response = self.client.post(
                self.url,
                data=self.message_data,
                format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("reply", response.data)
            self.assertIn("sources", response.data)
            self.assertIn("usage", response.data)
            self.assertEqual(response.data["reply"], self.mock_rag_response["answer"])

    def test_message_with_history(self):
        """Test message with conversation history"""
        from unittest.mock import patch
        
        message_with_history = {
            "message": "Tell me more",
            "history": [
                {"type": "user", "content": "What is AI?"},
                {"type": "bot", "content": "AI is artificial intelligence."}
            ]
        }
        
        with patch("apps.chatbot.views.chat_completion") as mock_chat:
            mock_chat.return_value = self.mock_rag_response
            
            response = self.client.post(
                self.url,
                data=message_with_history,
                format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Verify history was passed correctly
            call_args = mock_chat.call_args
            messages = call_args[1]["payload"]["messages"]
            self.assertEqual(len(messages), 3)  # 2 history + 1 current

    def test_empty_message(self):
        """Test with empty message"""
        response = self.client.post(
            self.url,
            data={"message": ""},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_no_chatbot_configured(self):
        """Test when chatbot doesn't exist"""
        # Delete chatbot
        self.chatbot.delete()
        
        response = self.client.post(
            self.url,
            data=self.message_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_llm_not_configured(self):
        """Test when LLM provider is not configured"""
        # Remove LLM configuration
        self.chatbot.llm_provider = None
        self.chatbot.save()
        
        response = self.client.post(
            self.url,
            data=self.message_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("LLM provider not configured", response.data["error"])

    def test_rag_error_handling(self):
        """Test error handling when RAG fails"""
        from unittest.mock import patch
        
        with patch("apps.chatbot.views.chat_completion") as mock_chat:
            mock_chat.side_effect = RuntimeError("LLM API error")
            
            response = self.client.post(
                self.url,
                data=self.message_data,
                format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        self.client.credentials()  # Remove authentication
        
        response = self.client.post(
            self.url,
            data=self.message_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_with_document_filters(self):
        """Test message with connected documents"""
        from unittest.mock import patch
        from apps.documents.models import Document
        
        # Create test documents
        doc1 = Document.objects.create(
            organization=self.org,
            name="Test Doc 1",
            file_type="pdf",
            size_bytes=1000,
            status="ready",
            url="http://example.com/doc1.pdf"
        )
        
        # Connect document to chatbot
        self.chatbot.documents_connected.add(doc1)
        
        with patch("apps.chatbot.views.chat_completion") as mock_chat:
            # Modify mock to include document in citations
            response_with_doc = self.mock_rag_response.copy()
            response_with_doc["citations"] = [
                {
                    "document_id": str(doc1.id),
                    "chunk_index": 0,
                    "content": "Content from doc",
                    "score": 0.95
                }
            ]
            mock_chat.return_value = response_with_doc
            
            response = self.client.post(
                self.url,
                data=self.message_data,
                format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("sources", response.data)
            self.assertIn("Test Doc 1", response.data["sources"])
            
            # Verify document filter was passed
            call_args = mock_chat.call_args
            filters = call_args[1]["payload"].get("filters")
            self.assertIsNotNone(filters)
            self.assertIn("document_ids", filters)
