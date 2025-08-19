from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from apps.documents.models import Document
from rest_framework_simplejwt.tokens import RefreshToken

class DocumentTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test document
        self.document = Document.objects.create(
            name='test.txt',
            content_type='text/plain',
            organization=self.organization,
            status='COMPLETED'
        )

    def test_list_documents(self):
        """Test listing documents"""
        url = reverse('document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'test.txt')

    def test_create_document(self):
        """Test uploading a new document"""
        url = reverse('document-list')
        file = SimpleUploadedFile(
            "test_doc.txt",
            b"Test content",
            content_type="text/plain"
        )
        data = {'file': file}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'test_doc.txt')
        self.assertEqual(response.data['status'], 'PENDING')

    def test_get_document_detail(self):
        """Test retrieving a single document"""
        url = reverse('document-detail', kwargs={'pk': self.document.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test.txt')

    def test_delete_document(self):
        """Test deleting a document"""
        url = reverse('document-detail', kwargs={'pk': self.document.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Document.objects.count(), 0)

    def test_reprocess_document(self):
        """Test reprocessing a document"""
        url = reverse('document-reprocess', kwargs={'pk': self.document.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'PENDING')

    def test_unauthorized_access(self):
        """Test unauthorized access to documents"""
        self.client.credentials()  # Remove authentication
        url = reverse('document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test accessing documents from wrong organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_doc = Document.objects.create(
            name='other.txt',
            content_type='text/plain',
            organization=other_org
        )
        url = reverse('document-detail', kwargs={'pk': other_doc.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
