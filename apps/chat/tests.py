from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.users.models import User
from apps.organizations.models import Organization
from apps.chatbot_provider.models import ChatbotProvider
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from django.test.utils import override_settings
import json
from django.utils import timezone
from datetime import timedelta
from apps.api_keys.models import APIKey

class BaseChatTestCase(APITestCase):
    """Base test case for chat tests with common setup"""
    
    def setUp(self):
        """Set up test data common to all chat tests"""
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Org',
            slug='test-org'
        )
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization,
            is_active=True
        )
        
        # Create test chatbot providers
        self.openai_provider = ChatbotProvider.objects.create(
            name='OpenAI Provider',
            provider_type='openai',
            api_key='test-openai-key',
            organization=self.organization,
            model='gpt-4',
            is_active=True
        )
        
        self.gemini_provider = ChatbotProvider.objects.create(
            name='Gemini Provider',
            provider_type='gemini',
            api_key='test-gemini-key',
            organization=self.organization,
            model='gemini-pro',
            is_active=True
        )
        
        # Create API key for testing
        self.api_key = APIKey.objects.create(
            name='Test API Key',
            organization=self.organization,
            created_by=self.user
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Common test data
        self.chat_data = {
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': 'What is the meaning of life?'}
            ],
            'max_tokens': 500,
            'temperature': 0.7,
            'provider_id': self.openai_provider.id
        }

class ChatCompletionTests(BaseChatTestCase):
    """Test cases for the chat completion endpoint"""
    
    def setUp(self):
        """Set up specific to chat completion tests"""
        super().setUp()
        self.url = reverse('chat-completions')
        self.mock_response = {
            'choices': [
                {
                    'message': {
                        'role': 'assistant',
                        'content': 'The meaning of life is 42.'
                    },
                    'finish_reason': 'stop'
                }
            ],
            'usage': {
                'prompt_tokens': 20,
                'completion_tokens': 10,
                'total_tokens': 30
            }
        }

    def test_successful_chat_completion(self):
        """Test successful chat completion with valid data"""
        with patch('apps.chat.services.chat_completion') as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY='test-key-1'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('choices', response.data)
            self.assertIn('usage', response.data)
            mock_chat.assert_called_once()

    def test_api_key_authentication(self):
        """Test chat completion using API key authentication"""
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        
        with patch('apps.chat.services.chat_completion') as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY='test-key-2'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, self.mock_response)

    def test_provider_specific_validation(self):
        """Test validation for different provider types"""
        # Test OpenAI specific parameters
        openai_data = {
            **self.chat_data,
            'provider_id': self.openai_provider.id,
            'presence_penalty': 0.5,
            'frequency_penalty': 0.5
        }
        
        with patch('apps.chat.services.chat_completion') as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=openai_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY='test-key-3'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test Gemini specific parameters
        gemini_data = {
            **self.chat_data,
            'provider_id': self.gemini_provider.id,
            'candidate_count': 1,
            'top_k': 40
        }
        
        with patch('apps.chat.services.chat_completion') as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=gemini_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY='test-key-4'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_message_format(self):
        """Test chat completion with invalid message format"""
        invalid_data = {
            **self.chat_data,
            'messages': [
                {'invalid_role': 'system', 'content': 'test'},  # Invalid role field
                {'role': 'user', 'wrong_field': 'test'}  # Missing content field
            ]
        }
        
        response = self.client.post(
            self.url,
            data=invalid_data,
            format='json',
            HTTP_IDEMPOTENCY_KEY='test-key-5'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_provider(self):
        """Test chat completion with inactive provider"""
        self.openai_provider.is_active = False
        self.openai_provider.save()
        
        response = self.client.post(
            self.url,
            data=self.chat_data,
            format='json',
            HTTP_IDEMPOTENCY_KEY='test-key-6'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_RATES': {'chat': '2/minute'}})
    def test_rate_limiting(self):
        """Test rate limiting for chat completion"""
        # Make requests up to limit
        for i in range(2):
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY=f'test-key-limit-{i}'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # This request should be throttled
        response = self.client.post(
            self.url,
            data=self.chat_data,
            format='json',
            HTTP_IDEMPOTENCY_KEY='test-key-limit-final'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_idempotency(self):
        """Test idempotency key functionality"""
        idem_key = 'test-idempotency-key'
        
        with patch('apps.chat.services.chat_completion') as mock_chat:
            mock_chat.return_value = self.mock_response
            
            # First request
            response1 = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY=idem_key
            )
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            
            # Second request with same key
            response2 = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_IDEMPOTENCY_KEY=idem_key
            )
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.assertEqual(response1.data, response2.data)
            
            # Mock should only be called once
            mock_chat.assert_called_once()

class ChatStreamTests(BaseChatTestCase):
    """Test cases for the chat streaming endpoint"""
    
    def setUp(self):
        """Set up specific to chat stream tests"""
        super().setUp()
        self.url = reverse('chat-stream')

    def test_successful_stream(self):
        """Test successful chat stream with valid data"""
        def mock_stream_generator():
            yield {"type": "message_start", "data": {}}
            yield {"type": "delta", "data": {"content": "Hello"}}
            yield {"type": "delta", "data": {"content": " World"}}
            yield {"type": "message_end", "data": {}}

        with patch('apps.chat.services.chat_stream') as mock_stream:
            mock_stream.return_value = mock_stream_generator()
            
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_ACCEPT='text/event-stream'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'text/event-stream')
            
            # Test streaming content
            content = b''.join(response.streaming_content)
            events = [json.loads(line.decode('utf-8').replace('data: ', ''))
                     for line in content.split(b'\n')
                     if line.startswith(b'data:')]
            
            self.assertEqual(len(events), 4)
            self.assertEqual(events[0]['type'], 'message_start')
            self.assertEqual(events[1]['type'], 'delta')
            self.assertEqual(events[2]['type'], 'delta')
            self.assertEqual(events[3]['type'], 'message_end')

    def test_stream_with_citations(self):
        """Test chat stream with citations"""
        def mock_stream_with_citations():
            yield {"type": "message_start", "data": {}}
            yield {"type": "delta", "data": {"content": "According to"}}
            yield {"type": "citation", "data": {"document_id": "doc1"}}
            yield {"type": "delta", "data": {"content": " the research"}}
            yield {"type": "message_end", "data": {}}

        with patch('apps.chat.services.chat_stream') as mock_stream:
            mock_stream.return_value = mock_stream_with_citations()
            
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_ACCEPT='text/event-stream'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = b''.join(response.streaming_content)
            events = [json.loads(line.decode('utf-8').replace('data: ', ''))
                     for line in content.split(b'\n')
                     if line.startswith(b'data:')]
            
            citation_event = next(e for e in events if e['type'] == 'citation')
            self.assertIn('document_id', citation_event['data'])

    def test_stream_error_handling(self):
        """Test error handling in streaming endpoint"""
        with patch('apps.chat.services.chat_stream') as mock_stream:
            mock_stream.side_effect = Exception("Stream error")
            
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_ACCEPT='text/event-stream'
            )
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_stream_connection_close(self):
        """Test proper handling of connection close"""
        def mock_stream_generator():
            yield {"type": "message_start", "data": {}}
            raise ConnectionError("Client disconnected")

        with patch('apps.chat.services.chat_stream') as mock_stream:
            mock_stream.return_value = mock_stream_generator()
            
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_ACCEPT='text/event-stream'
            )
            
            with self.assertRaises(ConnectionError):
                # Consuming the streaming content should raise the error
                list(response.streaming_content)

    @override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_RATES': {'chat': '2/minute'}})
    def test_stream_rate_limiting(self):
        """Test rate limiting for streaming endpoint"""
        # Make requests up to limit
        for _ in range(2):
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format='json',
                HTTP_ACCEPT='text/event-stream'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # This request should be throttled
        response = self.client.post(
            self.url,
            data=self.chat_data,
            format='json',
            HTTP_ACCEPT='text/event-stream'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
