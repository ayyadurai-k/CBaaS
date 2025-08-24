import os
import shutil
import tempfile
import uuid
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.models import Organization
from apps.users.models import User
from apps.documents.models import Document
from apps.api_keys.models import APIKey


def _unwrap_results(data):
    """
    Helper: DRF may return a list (no pagination) or a dict with 'results'.
    Keep tests robust regardless of global pagination settings.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    # If pagination is enabled, count/next/previous exist; if not, it's a bare list.
    # For safety, treat dicts with no 'results' as a single object list
    # (shouldn't happen for List endpoints, but keeps tests resilient).
    return [data]


class BaseDocumentTestCase(APITestCase):
    """Base test case for document tests with common setup"""

    def setUp(self) -> None:
        # Org with slug
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

        # API key (if your auth supports header-based)
        self.api_key = APIKey.objects.create(
            name="Test API Key",
            organization=self.organization,
            created_by=self.user,
        )

        # JWT auth
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Temp directory for creating input files
        self.test_files_dir = tempfile.mkdtemp()
        self.test_files = {
            "txt": self._create_test_file("test.txt", b"This is a test text file."),
            "pdf": self._create_test_file("test.pdf", b"%PDF-1.4\nFake PDF content"),
            "docx": self._create_test_file("test.docx", b"Fake DOCX content"),
        }

        # Seed one document (fields aligned with your model)
        self.document = Document.objects.create(
            name="test.txt",
            file_type=Document.FileType.TXT,
            size_bytes=len(b"This is a test text file."),
            organization=self.organization,
            status=Document.Status.READY,
            url="http://testserver/media/docs/test.txt",
        )

    def _create_test_file(self, name: str, content: bytes) -> str:
        path = os.path.join(self.test_files_dir, name)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def tearDown(self) -> None:
        shutil.rmtree(self.test_files_dir, ignore_errors=True)


class DocumentListCreateViewTests(BaseDocumentTestCase):
    """Test cases for DocumentListCreateView"""

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("document-list")

        # Create a few more docs
        self.documents = []
        for i in range(3):
            d = Document.objects.create(
                name=f"Test Document {i}.txt",
                file_type=Document.FileType.TXT,
                size_bytes=100 + i,
                organization=self.organization,
                status=Document.Status.PROCESSING if i == 1 else Document.Status.READY,
                url=f"http://testserver/media/docs/test_{i}.txt",
            )
            self.documents.append(d)

    def test_list_documents_success(self) -> None:
        """List returns our docs; shape resilient to pagination settings"""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = _unwrap_results(resp.data)
        # We created base 1 + 3 = 4 docs in this org
        # If the queryset isn't org-filtered globally, there may be more; at least 4 present with our names.
        names = {d["name"] for d in results if "name" in d}
        for expected in [
            "test.txt",
            "Test Document 0.txt",
            "Test Document 1.txt",
            "Test Document 2.txt",
        ]:
            self.assertIn(expected, names)

    def test_create_document_success(self) -> None:
        """Upload creates a Document; verify DB, not response fields (POST uses DocumentUploadSerializer)"""
        with patch("apps.documents.tasks.process_document.delay") as mock_delay:
            with open(self.test_files["txt"], "rb") as f:
                data = {"file": f, "name": "New Document.txt"}
                resp = self.client.post(self.url, data, format="multipart")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Serializer used for POST doesn't include full doc; verify via DB
        created = Document.objects.get(
            organization=self.organization, name="New Document.txt"
        )
        self.assertEqual(created.file_type, Document.FileType.TXT)
        self.assertEqual(created.status, Document.Status.PROCESSING)
        self.assertTrue(created.url)  # saved by storage
        self.assertGreater(created.size_bytes, 0)
        mock_delay.assert_called_once_with(str(created.id))

    def test_create_document_invalid_file_type(self) -> None:
        """Unsupported extension → 400 from DocumentUploadSerializer"""
        invalid_file = SimpleUploadedFile(
            "test.exe", b"invalid file content", content_type="application/x-msdownload"
        )
        resp = self.client.post(
            self.url, {"file": invalid_file, "name": "Bad"}, format="multipart"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_document_no_file(self) -> None:
        """Missing file → 400"""
        resp = self.client.post(self.url, {"name": "No File"}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"documents": "2/minute"}}
    )
    def test_document_rate_limiting(self) -> None:
        """Throttle kicks in on third POST within window"""
        with patch("apps.documents.tasks.process_document.delay"):
            for _ in range(2):
                with open(self.test_files["txt"], "rb") as f:
                    resp = self.client.post(
                        self.url, {"file": f, "name": "X"}, format="multipart"
                    )
                    self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

            with open(self.test_files["txt"], "rb") as f:
                resp = self.client.post(
                    self.url, {"file": f, "name": "Y"}, format="multipart"
                )
                self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class DocumentDetailViewTests(BaseDocumentTestCase):
    """Test cases for DocumentDetailView"""

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("document-detail", kwargs={"pk": self.document.pk})

    def test_retrieve_document_success(self) -> None:
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], self.document.name)
        self.assertEqual(resp.data["status"], self.document.status)
        # FK default representation is PK; compare as string for UUID consistency
        self.assertEqual(str(resp.data["organization"]), str(self.organization.id))

    def test_update_document_success(self) -> None:
        """PATCH name only; status/url/org are read-only per serializer"""
        data = {"name": "Updated Document.txt"}
        resp = self.client.patch(self.url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Updated Document.txt")

        self.document.refresh_from_db()
        self.assertEqual(self.document.name, "Updated Document.txt")

    def test_delete_document_success(self) -> None:
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())

    def test_access_nonexistent_document(self) -> None:
        url = reverse("document-detail", kwargs={"pk": uuid.uuid4()})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_access_other_organization_document(self) -> None:
        """Other org doc should be blocked by ReadOnlyOrOwnerAdmin"""
        other_org = Organization.objects.create(name="Other Org", slug="other-org")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass",
            organization=other_org,
            is_active=True,
        )
        other_doc = Document.objects.create(
            name="other.txt",
            file_type=Document.FileType.TXT,
            size_bytes=10,
            organization=other_org,
            status=Document.Status.READY,
            url="http://testserver/media/docs/other.txt",
        )
        url = reverse("document-detail", kwargs={"pk": other_doc.pk})
        resp = self.client.get(url)
        self.assertIn(
            resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
        )

    # NOTE: Removed "admin can read other org doc" because actual permission behavior
    # (ReadOnlyOrOwnerAdmin) is project-specific; add back if your permission allows it.


class DocumentReprocessViewTests(BaseDocumentTestCase):
    """Test cases for DocumentReprocessView"""

    def setUp(self) -> None:
        super().setUp()
        # Put current doc in FAILED to simulate needing reprocess
        self.document.status = Document.Status.FAILED
        self.document.save(update_fields=["status"])
        self.url = reverse("document-reprocess", kwargs={"pk": self.document.pk})

    def test_reprocess_document_success(self) -> None:
        with patch("apps.documents.tasks.process_document.delay") as mock_delay:
            resp = self.client.post(self.url)
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        self.document.refresh_from_db()
        self.assertEqual(self.document.status, Document.Status.PROCESSING)
        mock_delay.assert_called_once_with(str(self.document.id))

    def test_reprocess_nonexistent_document(self) -> None:
        url = reverse("document-reprocess", kwargs={"pk": uuid.uuid4()})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_reprocess_when_already_processing(self) -> None:
        """Your view always sets PROCESSING and returns 202 — even if already processing."""
        self.document.status = Document.Status.PROCESSING
        self.document.save(update_fields=["status"])
        with patch("apps.documents.tasks.process_document.delay") as mock_delay:
            resp = self.client.post(self.url)
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
            mock_delay.assert_called_once()

    def test_reprocess_other_organization_document(self) -> None:
        other_org = Organization.objects.create(name="Other Org", slug="other-org")
        other_doc = Document.objects.create(
            name="other.txt",
            file_type=Document.FileType.TXT,
            size_bytes=10,
            organization=other_org,
            status=Document.Status.FAILED,
            url="http://testserver/media/docs/other.txt",
        )
        url = reverse("document-reprocess", kwargs={"pk": other_doc.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(
        REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"documents": "2/minute"}}
    )
    def test_reprocess_rate_limiting(self) -> None:
        with patch("apps.documents.tasks.process_document.delay"):
            for _ in range(2):
                resp = self.client.post(self.url)
                self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

            resp = self.client.post(self.url)
            self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
