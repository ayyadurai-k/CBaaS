# tests.py
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

# Views under test
from apps.chatbot_provider.views import (
    TestKeyView,
    ChatbotProviderUpsertView,
)
from apps.chatbot_provider.serializers import (
    ProviderSerializer,
    ProviderUpsertSerializer,
)


class _AuthBase(APITestCase):
    """
    Creates an authenticated user and a lightweight org stub.
    Permissions are patched in individual tests to ensure deterministic outcomes.
    """

    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="u1", email="u1@example.com", password="strong-pass-123"
        )
        # Minimal org stub (views never hit DB for org due to patching Chatbot.*)
        self.org = SimpleNamespace(id=1, name="Acme")
        # Attach org attribute so view code can access request.user.organization
        setattr(self.user, "organization", self.org)

    # Helpers
    def _auth(self, request):
        force_authenticate(request, user=self.user)
        return request


class Test_TestKeyView(_AuthBase):
    """Covers permission behavior, payload validation, and 'no chatbot' vs 'ok' flows."""

    def test_forbidden_when_permission_denied(self):
        view = TestKeyView.as_view()
        payload = {"provider": "openai", "model_name": "gpt-4o", "api_key": "sk-123"}

        request = self._auth(self.factory.post("/api/chatbot/test-key", payload, format="json"))

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=False):
            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_400_when_chatbot_not_configured(self):
        view = TestKeyView.as_view()
        payload = {"provider": "openai", "model_name": "gpt-4o", "api_key": "sk-123"}
        request = self._auth(self.factory.post("/api/chatbot/test-key", payload, format="json"))

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot:
            # No chatbot for org
            Chatbot.objects.filter.return_value.first.return_value = None

            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Chatbot not configured")

    def test_200_ok_true_when_valid_and_bot_exists(self):
        view = TestKeyView.as_view()
        payload = {"provider": "openai", "model_name": "gpt-4o", "api_key": "sk-123"}
        request = self._auth(self.factory.post("/api/chatbot/test-key", payload, format="json"))

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot:
            # Simulate bot present
            Chatbot.objects.filter.return_value.first.return_value = Mock()

            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"ok": True})

    def test_400_when_invalid_provider_choice(self):
        view = TestKeyView.as_view()
        payload = {"provider": "not-a-provider", "model_name": "x", "api_key": "sk-123"}
        request = self._auth(self.factory.post("/api/chatbot/test-key", payload, format="json"))

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot:
            Chatbot.objects.filter.return_value.first.return_value = Mock()

            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # ProviderSerializer enforces the choices
        self.assertIn("provider", response.data)

    def test_400_when_missing_required_fields(self):
        view = TestKeyView.as_view()
        # Missing api_key
        payload = {"provider": "openai", "model_name": "gpt-4o"}
        request = self._auth(self.factory.post("/api/chatbot/test-key", payload, format="json"))

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot:
            Chatbot.objects.filter.return_value.first.return_value = Mock()

            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("api_key", response.data)


class Test_ChatbotProviderUpsertView(_AuthBase):
    """Covers create and update flows, serializer validation, and call contracts to Chatbot/Provider."""

    def _view_put(self, payload):
        view = ChatbotProviderUpsertView.as_view()
        request = self._auth(self.factory.put("/api/chatbot/provider", payload, format="json"))
        return view, request

    def test_forbidden_when_permission_denied(self):
        payload = {"provider": "openai", "model_name": "gpt-4o", "api_key": "sk-123"}
        view, request = self._view_put(payload)

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=False):
            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creates_new_provider_when_none_exists(self):
        payload = {"provider": "openai", "model_name": "gpt-4o", "api_key": "sk-secret"}
        view, request = self._view_put(payload)

        # Prepare mock provider instance returned by constructor
        provider_mock = Mock()
        provider_mock.id = uuid.uuid4()
        provider_mock.provider = payload["provider"]
        provider_mock.model_name = payload["model_name"]
        provider_mock.created_at = timezone.now()
        provider_mock.updated_at = timezone.now()

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot, \
             patch("apps.chatbot_provider.views.ChatbotProvider") as Provider:

            # Chatbot is created (get_or_create returns created=True)
            fake_bot = Mock()
            Chatbot.objects.get_or_create.return_value = (fake_bot, True)

            # No existing provider for this bot
            Provider.objects.filter.return_value.first.return_value = None

            # Provider(...) constructor returns our instance
            Provider.return_value = provider_mock

            response = view(request)

            # Assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["provider"], payload["provider"])
            self.assertEqual(response.data["model_name"], payload["model_name"])
            self.assertEqual(response.data["id"], str(provider_mock.id))
            self.assertIn("created_at", response.data)
            self.assertIn("updated_at", response.data)

            # Chatbot created with expected defaults (uses org.name in view)
            Chatbot.objects.get_or_create.assert_called_once()
            args, kwargs = Chatbot.objects.get_or_create.call_args
            self.assertIn("organization", kwargs)
            self.assertIs(kwargs["organization"], self.org)
            self.assertIn("defaults", kwargs)
            self.assertTrue(kwargs["defaults"]["name"].endswith(" Chatbot"))
            self.assertEqual(kwargs["defaults"]["tone"], "Technical")

            # Provider creation call contract: api_key is assigned via property after init
            Provider.assert_called_once()
            _, provider_kwargs = Provider.call_args
            self.assertEqual(provider_kwargs["chatbot"], fake_bot)
            self.assertEqual(provider_kwargs["provider"], payload["provider"])
            self.assertEqual(provider_kwargs["model_name"], payload["model_name"])

            # api_key must be set (property used in view)
            self.assertEqual(provider_mock.api_key, payload["api_key"])
            provider_mock.save.assert_called()

    def test_updates_existing_provider_when_present(self):
        payload = {"provider": "deepseek", "model_name": "deepseek-chat", "api_key": "sk-new"}
        view, request = self._view_put(payload)

        existing = Mock()
        existing.id = uuid.uuid4()
        existing.provider = "openai"
        existing.model_name = "gpt-4o"
        existing.created_at = timezone.now()
        existing.updated_at = timezone.now()

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot, \
             patch("apps.chatbot_provider.views.ChatbotProvider") as Provider:

            fake_bot = Mock()
            Chatbot.objects.get_or_create.return_value = (fake_bot, False)

            # Existing provider found
            Provider.objects.filter.return_value.first.return_value = existing

            response = view(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["id"], str(existing.id))
            self.assertEqual(response.data["provider"], payload["provider"])
            self.assertEqual(response.data["model_name"], payload["model_name"])

            # Serializer.update should have applied changes and saved
            self.assertEqual(existing.provider, payload["provider"])
            self.assertEqual(existing.model_name, payload["model_name"])
            self.assertEqual(existing.api_key, payload["api_key"])
            existing.save.assert_called()

    def test_400_when_invalid_provider_choice(self):
        payload = {"provider": "nope", "model_name": "m", "api_key": "sk-xyz"}
        view, request = self._view_put(payload)

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot, \
             patch("apps.chatbot_provider.views.ChatbotProvider") as Provider:

            Chatbot.objects.get_or_create.return_value = (Mock(), True)
            Provider.objects.filter.return_value.first.return_value = None

            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("provider", response.data)

    def test_400_when_missing_api_key(self):
        # ProviderUpsertSerializer requires api_key=True
        payload = {"provider": "openai", "model_name": "gpt-4o"}  # missing api_key
        view, request = self._view_put(payload)

        with patch("common.security.permissions.IsOwnerOrAdmin.has_permission", return_value=True), \
             patch("apps.chatbot_provider.views.Chatbot") as Chatbot, \
             patch("apps.chatbot_provider.views.ChatbotProvider") as Provider:

            Chatbot.objects.get_or_create.return_value = (Mock(), True)
            Provider.objects.filter.return_value.first.return_value = None

            response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("api_key", response.data)

    def test_serializer_contracts(self):
        """Sanity checks for serializer field contracts (choices, required flags, write_only)."""
        # ProviderSerializer: used in TestKeyView
        s1 = ProviderSerializer(data={"provider": "openai", "model_name": "gpt-4o", "api_key": "sk"})
        self.assertTrue(s1.is_valid(), s1.errors)
        self.assertIn("api_key", s1.fields)
        self.assertTrue(s1.fields["api_key"].write_only)

        # ProviderUpsertSerializer: api_key must be present, provider constrained by choices
        s2 = ProviderUpsertSerializer(data={"provider": "gemini", "model_name": "1.5-pro", "api_key": "sk"})
        self.assertTrue(s2.is_valid(), s2.errors)
        s3 = ProviderUpsertSerializer(data={"provider": "gemini", "model_name": "1.5-pro"})
        self.assertFalse(s3.is_valid())
        self.assertIn("api_key", s3.errors)
