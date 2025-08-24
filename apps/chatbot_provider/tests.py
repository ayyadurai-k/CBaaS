from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization
from apps.chatbot.models import Chatbot
from apps.chatbot_provider.models import ChatbotProvider
from apps.api_keys.models import APIKey
from apps.users.models import User


class BaseChatbotProviderTestCase(APITestCase):
    """Base test case for chatbot provider tests"""

    def setUp(self) -> None:
        # Org
        self.organization = Organization.objects.create(
            name="Test Org",
            slug="test-org",
        )

        # Users
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            organization=self.organization,
            is_active=True,
            is_staff=True,
        )

        # API key (for header-based auth path)
        self.api_key = APIKey.objects.create(
            name="Test API Key",
            organization=self.organization,
            created_by=self.user,
        )

        # Chatbot (provide required fields per your model)
        self.chatbot = Chatbot.objects.create(
            name="Test Chatbot",
            organization=self.organization,
            tone="Technical",
            system_instructions="Be helpful",
        )

        # Default auth via logged-in user
        self.client.force_authenticate(user=self.user)

        # Valid provider payloads (as required by ProviderUpsertSerializer)
        self.valid_providers = {
            "openai": {
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "sk-test-key",
            },
            "gemini": {
                "provider": "gemini",
                "model_name": "gemini-pro",
                "api_key": "test-key",
            },
            "deepseek": {
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "test-key",
            },
        }


class TestKeyViewTests(BaseChatbotProviderTestCase):
    """Tests for POST /test-key"""

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("test-key")

    def test_test_key_success(self) -> None:
        """All supported providers validate via serializer and return ok=True"""
        for data in self.valid_providers.values():
            resp = self.client.post(self.url, data, format="json")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(resp.data.get("ok", False))

    def test_test_key_no_chatbot(self) -> None:
        """If no chatbot configured for org, return 400 with specific message"""
        self.chatbot.delete()
        resp = self.client.post(self.url, self.valid_providers["openai"], format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("detail"), "Chatbot not configured")

    def test_test_key_invalid_provider(self) -> None:
        """Invalid provider choice should fail serializer validation"""
        bad = {"provider": "invalid", "model_name": "gpt-4", "api_key": "x"}
        resp = self.client.post(self.url, bad, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("provider", resp.data)

    def test_test_key_missing_fields(self) -> None:
        """Serializer complains on missing required fields"""
        base = self.valid_providers["openai"]

        for field in ("provider", "model_name", "api_key"):
            bad = {**base}
            del bad[field]
            resp = self.client.post(self.url, bad, format="json")
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, resp.data)

    def test_test_key_empty_api_key(self) -> None:
        """Empty string for api_key should be rejected"""
        bad = {**self.valid_providers["openai"], "api_key": ""}
        resp = self.client.post(self.url, bad, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("api_key", resp.data)

    def test_test_key_unauthenticated(self) -> None:
        """Unauthenticated request should be rejected"""
        self.client.force_authenticate(user=None)
        resp = self.client.post(self.url, self.valid_providers["openai"], format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_test_key_other_organization(self) -> None:
        """User from another org with no chatbot should get 400"""
        other_org = Organization.objects.create(name="Other Org", slug="other-org")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
            organization=other_org,
            is_active=True,
        )
        self.client.force_authenticate(user=other_user)
        resp = self.client.post(self.url, self.valid_providers["openai"], format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("detail"), "Chatbot not configured")

    def test_test_key_with_api_key_header(self) -> None:
        """Header-based API key auth path should also succeed (if permission allows)"""
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        resp = self.client.post(self.url, self.valid_providers["openai"], format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("ok", False))


class ChatbotProviderUpsertViewTests(BaseChatbotProviderTestCase):
    """Tests for PUT /provider-upsert"""

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("provider-upsert")
        # Single baseline payload
        self.valid_data = self.valid_providers["openai"]

    def test_create_provider_success_each_vendor(self) -> None:
        """Fresh creation for each provider should succeed"""
        ChatbotProvider.objects.all().delete()
        for data in self.valid_providers.values():
            resp = self.client.put(self.url, data, format="json")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(resp.data["provider"], data["provider"])
            self.assertEqual(resp.data["model_name"], data["model_name"])
            self.assertIn("id", resp.data)
            self.assertIn("created_at", resp.data)
            self.assertIn("updated_at", resp.data)

            # Verify DB persisted as expected
            obj = ChatbotProvider.objects.get(id=resp.data["id"])
            self.assertEqual(obj.chatbot, self.chatbot)
            self.assertEqual(obj.provider, data["provider"])
            self.assertEqual(obj.model_name, data["model_name"])
            # reset to test next vendor cleanly
            obj.delete()

    def test_update_provider_success(self) -> None:
        """Updating model_name on existing provider should retain same id"""
        create = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(create.status_code, status.HTTP_200_OK)
        provider_id = create.data["id"]

        update_payload = {
            "provider": "openai",
            "model_name": "gpt-4-turbo",
            "api_key": "new-secret",
        }
        upd = self.client.put(self.url, update_payload, format="json")
        self.assertEqual(upd.status_code, status.HTTP_200_OK)
        self.assertEqual(upd.data["id"], provider_id)
        self.assertEqual(upd.data["model_name"], "gpt-4-turbo")

        obj = ChatbotProvider.objects.get(id=provider_id)
        self.assertEqual(obj.model_name, "gpt-4-turbo")

    def test_create_provider_with_chatbot_auto_creation(self) -> None:
        """If no chatbot exists, view should create one with sane defaults"""
        self.chatbot.delete()
        resp = self.client.put(self.url, self.valid_providers["openai"], format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Use .get() to avoid OptionalMemberAccess (Pylance)
        bot = Chatbot.objects.get(organization=self.organization)
        self.assertEqual(bot.name, f"{self.organization.name} Chatbot")
        self.assertEqual(bot.organization, self.organization)

    def test_validation_errors(self) -> None:
        """Provider choices and required fields are enforced by the serializer"""
        bad_provider = {"provider": "invalid", "model_name": "gpt-4", "api_key": "x"}
        resp = self.client.put(self.url, bad_provider, format="json")
        I = status.HTTP_400_BAD_REQUEST
        self.assertEqual(resp.status_code, I)
        self.assertIn("provider", resp.data)

        empty_key = {**self.valid_data, "api_key": ""}
        resp = self.client.put(self.url, empty_key, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("api_key", resp.data)

        missing_fields = {"provider": "openai"}  # missing model_name, api_key
        resp = self.client.put(self.url, missing_fields, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("model_name", resp.data)
        self.assertIn("api_key", resp.data)

    def test_api_key_encryption_roundtrip(self) -> None:
        """Ciphertext stored; property returns plaintext"""
        resp = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        obj = ChatbotProvider.objects.get(id=resp.data["id"])
        # stored ciphertext is different from plaintext
        self.assertNotEqual(obj.api_key_encrypted, self.valid_data["api_key"])
        # property returns plaintext
        self.assertEqual(obj.api_key, self.valid_data["api_key"])
        # response should never expose api_key (write_only)
        self.assertNotIn("api_key", resp.data)

    def test_permissions(self) -> None:
        """Unauthenticated: 401; API key or admin user: 200"""
        # unauthenticated
        self.client.force_authenticate(user=None)
        resp = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # API key header (if your permission class supports it)
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        resp = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # admin user
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_concurrent_updates_timestamp_changes(self) -> None:
        """updated_at should move forward on subsequent updates"""
        first = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        initial_updated_at = first.data["updated_at"]

        # artificially advance DB field
        obj = ChatbotProvider.objects.get(id=first.data["id"])
        obj.updated_at = timezone.now() + timedelta(seconds=1)
        obj.save()

        second = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertNotEqual(second.data["updated_at"], initial_updated_at)

    def test_upsert_preserves_identity_across_provider_changes(self) -> None:
        """Switching provider should still update same row (single provider per bot)"""
        # openai
        r1 = self.client.put(self.url, self.valid_providers["openai"], format="json")
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        pid = r1.data["id"]

        # switch to gemini
        r2 = self.client.put(self.url, self.valid_providers["gemini"], format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data["id"], pid)
        self.assertEqual(r2.data["provider"], "gemini")

        # switch to deepseek
        r3 = self.client.put(self.url, self.valid_providers["deepseek"], format="json")
        self.assertEqual(r3.status_code, status.HTTP_200_OK)
        self.assertEqual(r3.data["id"], pid)
        self.assertEqual(r3.data["provider"], "deepseek")

    def test_invalid_method(self) -> None:
        """GET is not allowed on the upsert view"""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invalid_json_payload(self) -> None:
        """Bad JSON body should return 400 parse error"""
        resp = self.client.put(self.url, "not json", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_created_vs_updated_timestamps_order(self) -> None:
        """Basic sanity on timestamps ordering"""
        resp = self.client.put(self.url, self.valid_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        created = resp.data["created_at"]
        updated = resp.data["updated_at"]
        self.assertLessEqual(created, updated)

    def test_case_and_whitespace_rules(self) -> None:
        """Provider must match choices exactly (lowercase, no surrounding spaces)"""
        bad_upper = {**self.valid_data, "provider": "OPENAI"}
        resp = self.client.put(self.url, bad_upper, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        bad_space = {**self.valid_data, "provider": " openai "}
        resp = self.client.put(self.url, bad_space, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
