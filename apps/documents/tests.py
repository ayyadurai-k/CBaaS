from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.users.models import User
from apps.organizations.models import Organization
from apps.documents.models import Document
from apps.api_keys.models import APIKey
from apps.documents.tasks import process_document
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

class BaseDocumentTestCase(APITestCase):
    """Base test case for document tests with common setup"""
    
    def setUp(self):
        """Set up test data common to all document tests"""
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
        
        # Set up JWT authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Set up test files directory
        self.test_files_dir = tempfile.mkdtemp()
        
        # Create various test files
        self.test_files = {
            'txt': self._create_test_file('test.txt', b'This is a test text file.'),
            'pdf': self._create_test_file('test.pdf', b'%PDF-1.4\nFake PDF content'),
            'docx': self._create_test_file('test.docx', b'Fake DOCX content'),
            'large': self._create_test_file('large.txt', b'x' * 1024 * 1024)  # 1MB file
        }
        
        # Create a test document
        self.document = Document.objects.create(
            name='test.txt',
            file_type='txt',
            content_type='text/plain',
            size_bytes=len(b'This is a test text file.'),
            organization=self.organization,
            uploaded_by=self.user,
            status=Document.Status.PROCESSED
        )

    def _create_test_file(self, name, content):
        """Helper to create a test file"""
        path = os.path.join(self.test_files_dir, name)
        with open(path, 'wb') as f:
            f.write(content)
        return path

    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.test_files_dir)

class DocumentListCreateViewTests(BaseDocumentTestCase):
    """Test cases for DocumentListCreateView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('document-list')
        
        # Create additional test documents
        self.documents = []
        for i in range(3):
            doc = Document.objects.create(
                name=f'Test Document {i}.txt',
                file_type='txt',
                content_type='text/plain',
                size_bytes=100,
                organization=self.organization,
                uploaded_by=self.user,
                status=Document.Status.PROCESSED if i != 1 else Document.Status.PROCESSING
            )
            self.documents.append(doc)

    def test_list_documents_success(self):
        """Test successful document listing"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)  # 3 + 1 from base setup
        
        # Check pagination
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_list_documents_filtering(self):
        """Test document list filtering"""
        # Test status filter
        response = self.client.get(f'{self.url}?status=processing')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], Document.Status.PROCESSING)
        
        # Test name filter
        response = self.client.get(f'{self.url}?search=Document 0')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Document 0.txt')
        
        # Test file type filter
        response = self.client.get(f'{self.url}?file_type=txt')
        self.assertTrue(all(doc['file_type'] == 'txt' for doc in response.data['results']))

    def test_list_documents_ordering(self):
        """Test document list ordering"""
        # Test ordering by name ascending
        response = self.client.get(f'{self.url}?ordering=name')
        names = [doc['name'] for doc in response.data['results']]
        self.assertEqual(names, sorted(names))
        
        # Test ordering by upload date descending
        response = self.client.get(f'{self.url}?ordering=-upload_date')
        dates = [doc['upload_date'] for doc in response.data['results']]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_create_document_success(self):
        """Test successful document creation"""
        with open(self.test_files['txt'], 'rb') as file:
            data = {
                'file': file,
                'name': 'New Document.txt',
                'description': 'Test description'
            }
            response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Document.txt')
        self.assertEqual(response.data['status'], Document.Status.PROCESSING)
        self.assertEqual(response.data['description'], 'Test description')
        
        # Verify process_document task was called
        doc = Document.objects.get(id=response.data['id'])
        self.assertTrue(hasattr(doc, 'file'))
        self.assertEqual(doc.organization, self.organization)
        self.assertEqual(doc.uploaded_by, self.user)

    def test_create_document_with_api_key(self):
        """Test document creation using API key authentication"""
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        
        with open(self.test_files['txt'], 'rb') as file:
            data = {'file': file}
            response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(id=response.data['id'])
        self.assertEqual(doc.organization, self.organization)

    def test_create_document_invalid_file_type(self):
        """Test document creation with invalid file type"""
        # Create file with invalid extension
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"invalid file content",
            content_type="application/x-msdownload"
        )
        
        data = {'file': invalid_file}
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    @override_settings(MAX_UPLOAD_SIZE=500*1024)  # Set max upload size to 500KB
    def test_create_document_file_too_large(self):
        """Test document creation with file exceeding size limit"""
        with open(self.test_files['large'], 'rb') as file:
            data = {'file': file}
            response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    def test_create_document_no_file(self):
        """Test document creation without file"""
        data = {'name': 'No File Document'}
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    @override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_RATES': {'documents': '2/minute'}})
    def test_document_rate_limiting(self):
        """Test rate limiting for document operations"""
        # Make requests up to limit
        for i in range(2):
            with open(self.test_files['txt'], 'rb') as file:
                data = {'file': file}
                response = self.client.post(self.url, data, format='multipart')
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # This request should be throttled
        with open(self.test_files['txt'], 'rb') as file:
            data = {'file': file}
            response = self.client.post(self.url, data, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class DocumentDetailViewTests(BaseDocumentTestCase):
    """Test cases for DocumentDetailView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('document-detail', kwargs={'pk': self.document.pk})

    def test_retrieve_document_success(self):
        """Test successful document retrieval"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.document.name)
        self.assertEqual(response.data['status'], self.document.status)
        self.assertEqual(response.data['organization'], self.organization.id)

    def test_update_document_success(self):
        """Test successful document update"""
        data = {
            'name': 'Updated Document.txt',
            'description': 'Updated description'
        }
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Document.txt')
        self.assertEqual(response.data['description'], 'Updated description')
        
        # Verify database update
        self.document.refresh_from_db()
        self.assertEqual(self.document.name, 'Updated Document.txt')
        self.assertEqual(self.document.description, 'Updated description')

    def test_delete_document_success(self):
        """Test successful document deletion"""
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())

    def test_access_nonexistent_document(self):
        """Test accessing a nonexistent document"""
        url = reverse('document-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_access_other_organization_document(self):
        """Test accessing document from another organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            organization=other_org
        )
        
        # Create document in other organization
        other_doc = Document.objects.create(
            name='other.txt',
            file_type='txt',
            organization=other_org,
            uploaded_by=other_user,
            status=Document.Status.PROCESSED
        )
        
        url = reverse('document-detail', kwargs={'pk': other_doc.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_access_other_org_document(self):
        """Test admin access to document from another organization"""
        # Switch to admin user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.admin_user).access_token)}')
        
        other_org = Organization.objects.create(name='Other Org')
        other_doc = Document.objects.create(
            name='other.txt',
            file_type='txt',
            organization=other_org,
            status=Document.Status.PROCESSED
        )
        
        url = reverse('document-detail', kwargs={'pk': other_doc.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class DocumentReprocessViewTests(BaseDocumentTestCase):
    """Test cases for DocumentReprocessView"""
    
    def setUp(self):
        super().setUp()
        self.document.status = Document.Status.ERROR
        self.document.save()
        self.url = reverse('document-reprocess', kwargs={'pk': self.document.pk})

    def test_reprocess_document_success(self):
        """Test successful document reprocessing"""
        with patch('apps.documents.tasks.process_document.delay') as mock_process:
            response = self.client.post(self.url)
            
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            
            # Verify document status updated
            self.document.refresh_from_db()
            self.assertEqual(self.document.status, Document.Status.PROCESSING)
            
            # Verify task called
            mock_process.assert_called_once_with(str(self.document.id))

    def test_reprocess_nonexistent_document(self):
        """Test reprocessing nonexistent document"""
        url = reverse('document-reprocess', kwargs={'pk': 99999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reprocess_processing_document(self):
        """Test reprocessing a document that's already processing"""
        self.document.status = Document.Status.PROCESSING
        self.document.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reprocess_other_organization_document(self):
        """Test reprocessing document from another organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_doc = Document.objects.create(
            name='other.txt',
            file_type='txt',
            organization=other_org,
            status=Document.Status.ERROR
        )
        
        url = reverse('document-reprocess', kwargs={'pk': other_doc.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_RATES': {'documents': '2/minute'}})
    def test_reprocess_rate_limiting(self):
        """Test rate limiting for document reprocessing"""
        # Make requests up to limit
        for _ in range(2):
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # This request should be throttled
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
