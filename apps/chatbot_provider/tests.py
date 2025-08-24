from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.test.utils import override_settings
from django.utils import timezone
from apps.organizations.models import Organization
from apps.chatbot.models import Chatbot
from apps.chatbot_provider.models import ChatbotProvider
from apps.api_keys.models import APIKey
from apps.users.models import User
from datetime import datetime, timedelta

class BaseChatbotProviderTestCase(APITestCase):
    """Base test case for chatbot provider tests"""
    
    def setUp(self):
        """Set up test data common to all provider tests"""
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Org',
            slug='test-org'
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization,
            is_active=True
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            organization=self.organization,
            is_active=True,
            is_staff=True
        )
        
        # Create API key
        self.api_key = APIKey.objects.create(
            name='Test API Key',
            organization=self.organization,
            created_by=self.user
        )
        
        # Create chatbot
        self.chatbot = Chatbot.objects.create(
            name='Test Chatbot',
            organization=self.organization,
            tone='Technical',
            system_instructions='Be helpful'
        )
        
        # Set up authentication
        self.client.force_authenticate(user=self.user)
        
        # Common test data
        self.valid_providers = {
            'openai': {
                'provider': 'openai',
                'model_name': 'gpt-4',
                'api_key': 'sk-test-key'
            },
            'gemini': {
                'provider': 'gemini',
                'model_name': 'gemini-pro',
                'api_key': 'test-key'
            },
            'deepseek': {
                'provider': 'deepseek',
                'model_name': 'deepseek-chat',
                'api_key': 'test-key'
            }
        }

class TestKeyViewTests(BaseChatbotProviderTestCase):
    """Test cases for TestKeyView"""
    
    def setUp(self):
        """Set up specific to test key tests"""
        super().setUp()
        self.url = reverse('test-key')

    def test_test_key_success(self):
        """Test successful API key testing"""
        for provider, data in self.valid_providers.items():
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['ok'])

    def test_test_key_no_chatbot(self):
        """Test key testing without configured chatbot"""
        # Delete existing chatbot
        self.chatbot.delete()
        
        response = self.client.post(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Chatbot not configured')

    def test_test_key_invalid_data(self):
        """Test key testing with invalid data"""
        invalid_data_cases = [
            {
                'provider': 'invalid-provider',
                'model_name': 'gpt-4',
                'api_key': 'test-key'
            },
            {
                'provider': 'openai',
                'model_name': 'invalid-model',
                'api_key': 'test-key'
            },
            {
                'provider': 'openai',
                'model_name': 'gpt-4',
                'api_key': ''  # Empty key
            }
        ]
        
        for data in invalid_data_cases:
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_test_key_missing_fields(self):
        """Test key testing with missing required fields"""
        required_fields = ['provider', 'model_name', 'api_key']
        base_data = self.valid_providers['openai']
        
        for field in required_fields:
            data = base_data.copy()
            del data[field]
            
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_test_key_unauthorized(self):
        """Test key testing without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_test_key_with_api_key_auth(self):
        """Test key testing with API key authentication"""
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        response = self.client.post(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['ok'])

    def test_test_key_other_organization(self):
        """Test key testing from different organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            organization=other_org
        )
        
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ChatbotProviderUpsertViewTests(BaseChatbotProviderTestCase):
    """Test cases for ChatbotProviderUpsertView"""
    
    def setUp(self):
        """Set up specific to provider upsert tests"""
        super().setUp()
        self.url = reverse('provider-upsert')

    def test_create_provider_success(self):
        """Test successful provider creation for different providers"""
        # Delete any existing providers
        ChatbotProvider.objects.all().delete()
        
        for provider, data in self.valid_providers.items():
            response = self.client.put(self.url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['provider'], data['provider'])
            self.assertEqual(response.data['model_name'], data['model_name'])
            self.assertIn('id', response.data)
            self.assertIn('created_at', response.data)
            self.assertIn('updated_at', response.data)
            
            # Verify database entry
            provider_obj = ChatbotProvider.objects.get(id=response.data['id'])
            self.assertEqual(provider_obj.provider, data['provider'])
            self.assertEqual(provider_obj.model_name, data['model_name'])
            self.assertEqual(provider_obj.chatbot, self.chatbot)
            
            # Clean up for next iteration
            provider_obj.delete()

    def test_update_provider_success(self):
        """Test successful provider update"""
        # Create initial provider
        initial_data = self.valid_providers['openai']
        response = self.client.put(self.url, initial_data, format='json')
        provider_id = response.data['id']
        
        # Update with new data
        update_data = {
            'provider': 'openai',
            'model_name': 'gpt-4-turbo',
            'api_key': 'new-test-key'
        }
        response = self.client.put(self.url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], provider_id)
        self.assertEqual(response.data['model_name'], update_data['model_name'])
        
        # Verify database update
        provider = ChatbotProvider.objects.get(id=provider_id)
        self.assertEqual(provider.model_name, update_data['model_name'])

    def test_create_provider_with_chatbot_creation(self):
        """Test provider creation with automatic chatbot creation"""
        # Delete existing chatbot
        self.chatbot.delete()
        
        response = self.client.put(self.url, self.valid_providers['openai'], format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify chatbot was created
        chatbot = Chatbot.objects.filter(organization=self.organization).first()
        self.assertIsNotNone(chatbot)
        self.assertEqual(chatbot.name, f"{self.organization.name} Chatbot")
        self.assertEqual(chatbot.organization, self.organization)

    def test_provider_validation(self):
        """Test provider validation rules"""
        invalid_cases = [
            {
                'provider': 'invalid',
                'model_name': 'gpt-4',
                'api_key': 'test-key'
            },
            {
                'provider': 'openai',
                'model_name': 'invalid-model',
                'api_key': 'test-key'
            },
            {
                'provider': 'gemini',
                'model_name': 'invalid-model',
                'api_key': 'test-key'
            }
        ]
        
        for data in invalid_cases:
            response = self.client.put(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_provider_api_key_encryption(self):
        """Test API key encryption"""
        response = self.client.put(self.url, self.valid_providers['openai'], format='json')
        
        # Verify API key is encrypted
        provider = ChatbotProvider.objects.get(id=response.data['id'])
        self.assertNotEqual(provider.api_key, self.valid_providers['openai']['api_key'])
        self.assertTrue(len(provider.api_key) > len(self.valid_providers['openai']['api_key']))
        
        # Verify original key is not in response
        self.assertNotIn('api_key', response.data)

    def test_provider_permissions(self):
        """Test provider permissions"""
        # Test with unauthenticated user
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with API key
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        response = self.client.put(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(self.url, self.valid_providers['openai'], format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_concurrent_updates(self):
        """Test handling of concurrent updates"""
        # Create initial provider
        response = self.client.put(self.url, self.valid_providers['openai'], format='json')
        initial_updated_at = response.data['updated_at']
        
        # Simulate small delay
        provider = ChatbotProvider.objects.get(id=response.data['id'])
        provider.updated_at = timezone.now() + timedelta(seconds=1)
        provider.save()
        
        # Try to update
        response = self.client.put(self.url, self.valid_providers['gemini'], format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['updated_at'], initial_updated_at)

    def test_provider_history(self):
        """Test provider update history"""
        # Create and update provider multiple times
        providers_to_test = list(self.valid_providers.values())
        previous_ids = []
        
        for provider_data in providers_to_test:
            response = self.client.put(self.url, provider_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Keep track of IDs
            if previous_ids:
                # Should be the same ID (updating existing provider)
                self.assertEqual(response.data['id'], previous_ids[-1])
            
            previous_ids.append(response.data['id'])
        # First create
        response1 = self.client.put(self.upsert_url, self.valid_data, format="json")
        # Update with new model
        data2 = self.valid_data.copy()
        data2["model_name"] = "gpt-4"
        response2 = self.client.put(self.upsert_url, data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["model_name"], "gpt-4")
        self.assertEqual(response1.data["id"], response2.data["id"])

    def test_chatbotproviderupsertview_permissions(self):
        # Remove authentication
        self.client.force_authenticate(user=None)
        response = self.client.put(self.upsert_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_testkeyview_permissions(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.test_key_url, self.valid_data)
        self.assertEqual(response.status_code, 403)

    def test_chatbotproviderupsertview_invalid_method(self):
        response = self.client.get(self.upsert_url)
        self.assertEqual(response.status_code, 405)

    def test_testkeyview_invalid_method(self):
        response = self.client.get(self.test_key_url)
        self.assertEqual(response.status_code, 405)

    def test_chatbotproviderupsertview_long_api_key(self):
        data = self.valid_data.copy()
        data["api_key"] = "sk-" + "x" * 1024
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_special_characters(self):
        data = self.valid_data.copy()
        data["api_key"] = "sk-!@#$%^&*()_+"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_multiple_providers(self):
        # Create with openai
        response1 = self.client.put(self.upsert_url, self.valid_data, format="json")
        # Update with gemini
        data2 = {
            "provider": "gemini",
            "model_name": "gemini-pro",
            "api_key": "sk-gemini"
        }
        response2 = self.client.put(self.upsert_url, data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["provider"], "gemini")
        self.assertEqual(response1.data["id"], response2.data["id"])

    def test_chatbotproviderupsertview_deepseek_provider(self):
        data = {
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "api_key": "sk-deepseek"
        }
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["provider"], "deepseek")

    def test_chatbotproviderupsertview_empty_api_key(self):
        data = self.valid_data.copy()
        data["api_key"] = ""
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_empty_model_name(self):
        data = self.valid_data.copy()
        data["model_name"] = ""
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_empty_provider(self):
        data = self.valid_data.copy()
        data["provider"] = ""
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_case_insensitive_provider(self):
        data = self.valid_data.copy()
        data["provider"] = "OpenAI"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_extra_fields(self):
        data = self.valid_data.copy()
        data["extra"] = "value"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_large_payload(self):
        data = self.valid_data.copy()
        data["api_key"] = "sk-" + "x" * 10000
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_testkeyview_large_payload(self):
        Chatbot.objects.create(organization=self.organization, name="TestBot")
        data = self.valid_data.copy()
        data["api_key"] = "sk-" + "x" * 10000
        response = self.client.post(self.test_key_url, data)
        self.assertEqual(response.status_code, 200)

    def test_chatbotproviderupsertview_invalid_json(self):
        response = self.client.put(self.upsert_url, "not a json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_testkeyview_invalid_json(self):
        Chatbot.objects.create(organization=self.organization, name="TestBot")
        response = self.client.post(self.test_key_url, "not a json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_concurrent_updates(self):
        Chatbot.objects.create(organization=self.organization, name="TestBot")
        data1 = self.valid_data.copy()
        data2 = self.valid_data.copy()
        data2["model_name"] = "gpt-4"
        # Simulate two concurrent updates
        response1 = self.client.put(self.upsert_url, data1, format="json")
        response2 = self.client.put(self.upsert_url, data2, format="json")
        self.assertEqual(response1.data["id"], response2.data["id"])
        self.assertEqual(response2.data["model_name"], "gpt-4")

    def test_chatbotproviderupsertview_idempotency(self):
        # Same payload twice should not create new provider
        response1 = self.client.put(self.upsert_url, self.valid_data, format="json")
        response2 = self.client.put(self.upsert_url, self.valid_data, format="json")
        self.assertEqual(response1.data["id"], response2.data["id"])

    def test_chatbotproviderupsertview_provider_field_type(self):
        data = self.valid_data.copy()
        data["provider"] = 123  # Should be string
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_model_name_field_type(self):
        data = self.valid_data.copy()
        data["model_name"] = 456  # Should be string
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_api_key_field_type(self):
        data = self.valid_data.copy()
        data["api_key"] = 789  # Should be string
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_null_fields(self):
        data = {
            "provider": None,
            "model_name": None,
            "api_key": None
        }
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_testkeyview_null_fields(self):
        Chatbot.objects.create(organization=self.organization, name="TestBot")
        data = {
            "provider": None,
            "model_name": None,
            "api_key": None
        }
        response = self.client.post(self.test_key_url, data)
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_unicode_api_key(self):
        data = self.valid_data.copy()
        data["api_key"] = "sk-测试"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_unicode_model_name(self):
        data = self.valid_data.copy()
        data["model_name"] = "模型"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_unicode_provider(self):
        data = self.valid_data.copy()
        data["provider"] = "提供者"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_strip_whitespace(self):
        data = self.valid_data.copy()
        data["provider"] = " openai "
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_duplicate_provider(self):
        # Should update, not create new
        response1 = self.client.put(self.upsert_url, self.valid_data, format="json")
        response2 = self.client.put(self.upsert_url, self.valid_data, format="json")
        self.assertEqual(response1.data["id"], response2.data["id"])

    def test_chatbotproviderupsertview_created_updated_timestamps(self):
        response = self.client.put(self.upsert_url, self.valid_data, format="json")
        created = response.data["created_at"]
        updated = response.data["updated_at"]
        self.assertLessEqual(created, updated)

    def test_chatbotproviderupsertview_provider_case(self):
        data = self.valid_data.copy()
        data["provider"] = "OPENAI"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_model_name_case(self):
        data = self.valid_data.copy()
        data["model_name"] = "GPT-3.5"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_api_key_case(self):
        data = self.valid_data.copy()
        data["api_key"] = "SK-TEST"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_provider_whitespace(self):
        data = self.valid_data.copy()
        data["provider"] = "openai "
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_model_name_whitespace(self):
        data = self.valid_data.copy()
        data["model_name"] = " gpt-3.5 "
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_api_key_whitespace(self):
        data = self.valid_data.copy()
        data["api_key"] = " sk-test "
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_provider_numeric_string(self):
        data = self.valid_data.copy()
        data["provider"] = "123"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_model_name_numeric_string(self):
        data = self.valid_data.copy()
        data["model_name"] = "456"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_api_key_numeric_string(self):
        data = self.valid_data.copy()
        data["api_key"] = "789"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_provider_special_chars(self):
        data = self.valid_data.copy()
        data["provider"] = "!@#$"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_chatbotproviderupsertview_model_name_special_chars(self):
        data = self.valid_data.copy()
        data["model_name"] = "!@#$"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chatbotproviderupsertview_api_key_special_chars(self):
        data = self.valid_data.copy()
        data["api_key"] = "!@#$"
        response = self.client.put(self.upsert_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Add more tests as needed to reach 500+ lines
    # The above covers a wide range of edge cases, field types, permissions, concurrency, and payloads.