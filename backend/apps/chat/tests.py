from typing import cast, Iterator
import json

from django.http import StreamingHttpResponse
from django.urls import reverse
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.users.models import User
from apps.organizations.models import Organization
from apps.chatbot.models import Chatbot
from apps.api_keys.models import APIKey
from rest_framework_simplejwt.tokens import RefreshToken


class BaseChatTestCase(APITestCase):
    """Base test case for chat tests with common setup"""

    def setUp(self) -> None:
        # Organization
        self.organization = Organization.objects.create(
            name="Test Org",
            slug="test-org",
        )

        # User
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True,
        )

        # Chatbot (linked to org) with LLM provider configured
        self.chatbot = Chatbot.objects.create(
            organization=self.organization,
            name="Org Bot",
            tone="technical",
            system_instructions="You are a helpful assistant.",
            llm_provider="openai",
            llm_model="gpt-4",
            llm_is_active=True,
        )
        # Set encrypted API key
        self.chatbot.llm_api_key = "test-openai-key"
        self.chatbot.save()

        # Project-level API key
        self.api_key = APIKey.objects.create(
            name="Test API Key",
            organization=self.organization,
            created_by=self.user,
        )

        # JWT auth
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Common chat payload (updated for RAG)
        self.chat_data = {
            "messages": [
                {"role": "user", "content": "What is the meaning of life?"},
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "top_k": 6,
        }


class ChatCompletionTests(BaseChatTestCase):
    """Test cases for the chat completion endpoint"""

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("chat-completions")
        # Mock response matching chat_completion return format
        self.mock_response = {
            "id": "resp_1234567890",
            "session_id": None,
            "model": "gpt-4",
            "answer": "The meaning of life is 42.",
            "citations": [
                {
                    "document_id": "doc-123",
                    "chunk_index": 0,
                    "content": "Some relevant content",
                    "score": 0.95
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "total_tokens": 30,
            },
            "latency_ms": 150,
        }

    def test_successful_chat_completion(self) -> None:
        with patch("apps.chat.services.chat_completion") as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY="test-key-1",
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("answer", response.data)
            self.assertIn("citations", response.data)
            self.assertIn("usage", response.data)
            mock_chat.assert_called_once()

    def test_api_key_authentication(self) -> None:
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        with patch("apps.chat.services.chat_completion") as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY="test-key-2",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("answer", response.data)
            self.assertIn("usage", response.data)

    def test_rag_with_filters(self) -> None:
        # Test with document filters
        filtered_data = {
            **self.chat_data,
            "filters": {
                "document_ids": ["doc-123"],
                "file_types": ["pdf"]
            }
        }
        with patch("apps.chat.services.chat_completion") as mock_chat:
            mock_chat.return_value = self.mock_response
            response = self.client.post(
                self.url,
                data=filtered_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY="test-key-3",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("citations", response.data)

    def test_invalid_message_format(self) -> None:
        invalid_data = {
            **self.chat_data,
            "messages": [
                {"invalid_role": "system", "content": "test"},
                {"role": "user", "wrong_field": "test"},
            ],
        }
        response = self.client.post(
            self.url,
            data=invalid_data,
            format="json",
            HTTP_IDEMPOTENCY_KEY="test-key-5",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unconfigured_provider(self) -> None:
        # Remove LLM configuration
        self.chatbot.llm_provider = None
        self.chatbot.save()

        response = self.client.post(
            self.url,
            data=self.chat_data,
            format="json",
            HTTP_IDEMPOTENCY_KEY="test-key-6",
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"chat": "2/minute"}})
    def test_rate_limiting(self) -> None:
        for i in range(2):
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY=f"test-key-limit-{i}",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.url,
            data=self.chat_data,
            format="json",
            HTTP_IDEMPOTENCY_KEY="test-key-limit-final",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_idempotency(self) -> None:
        idem_key = "test-idempotency-key"
        with patch("apps.chat.services.chat_completion") as mock_chat:
            mock_chat.return_value = self.mock_response

            response1 = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY=idem_key,
            )
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

            response2 = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY=idem_key,
            )
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.assertEqual(response1.data, response2.data)
            mock_chat.assert_called_once()


class ChatStreamTests(BaseChatTestCase):
    """Test cases for the chat streaming endpoint"""

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("chat-stream")

    def test_successful_stream(self) -> None:
        def mock_stream_generator():
            yield {"type": "message_start", "data": {}}
            yield {"type": "delta", "data": {"content": "Hello"}}
            yield {"type": "delta", "data": {"content": " World"}}
            yield {"type": "message_end", "data": {}}

        with patch("apps.chat.services.chat_stream") as mock_stream:
            mock_stream.return_value = mock_stream_generator()

            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("text/event-stream", response["Content-Type"])

            streaming_response = cast(StreamingHttpResponse, response)
            content = b"".join(
                cast(Iterator[bytes], streaming_response.streaming_content)
            )
            events = [
                json.loads(line.decode("utf-8").replace("data: ", ""))
                for line in content.split(b"\n")
                if line.startswith(b"data:")
            ]

            event_types = [e.get("type") for e in events]
            self.assertIn("message_start", event_types)
            self.assertIn("delta", event_types)
            self.assertIn("message_end", event_types)

    def test_stream_with_citations(self) -> None:
        def mock_stream_with_citations():
            yield {"type": "message_start", "data": {}}
            yield {"type": "delta", "data": {"content": "According to"}}
            yield {"type": "citation", "data": {"document_id": "doc1"}}
            yield {"type": "delta", "data": {"content": " the research"}}
            yield {"type": "message_end", "data": {}}

        with patch("apps.chat.services.chat_stream") as mock_stream:
            mock_stream.return_value = mock_stream_with_citations()

            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            streaming_response = cast(StreamingHttpResponse, response)
            content = b"".join(
                cast(Iterator[bytes], streaming_response.streaming_content)
            )
            events = [
                json.loads(line.decode("utf-8").replace("data: ", ""))
                for line in content.split(b"\n")
                if line.startswith(b"data:")
            ]
            citation_event = next(e for e in events if e.get("type") == "citation")
            self.assertIn("document_id", citation_event["data"])

    def test_stream_error_handling(self) -> None:
        with patch("apps.chat.services.chat_stream") as mock_stream:
            mock_stream.side_effect = Exception("Stream error")

            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )

            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def test_stream_connection_close(self) -> None:
        def mock_stream_generator():
            yield {"type": "message_start", "data": {}}
            raise ConnectionError("Client disconnected")

        with patch("apps.chat.services.chat_stream") as mock_stream:
            mock_stream.return_value = mock_stream_generator()

            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )

            streaming_response = cast(StreamingHttpResponse, response)
            with self.assertRaises(ConnectionError):
                list(cast(Iterator[bytes], streaming_response.streaming_content))

    @override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"chat": "2/minute"}})
    def test_stream_rate_limiting(self) -> None:
        for _ in range(2):
            response = self.client.post(
                self.url,
                data=self.chat_data,
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.url,
            data=self.chat_data,
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
