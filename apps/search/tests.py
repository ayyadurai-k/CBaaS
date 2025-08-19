from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from apps.documents.models import Document
from rest_framework_simplejwt.tokens import RefreshToken

class SearchTests(APITestCase):
    def setUp(self):
        # Create test user and organization
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
        
        # Create test documents
        self.document1 = Document.objects.create(
            name='test1.txt',
            content_type='text/plain',
            organization=self.organization,
            status='COMPLETED',
            content='This is a test document about artificial intelligence.'
        )
        
        self.document2 = Document.objects.create(
            name='test2.txt',
            content_type='text/plain',
            organization=self.organization,
            status='COMPLETED',
            content='This document contains information about machine learning.'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_semantic_search(self):
        """Test semantic search functionality"""
        url = reverse('search')
        data = {
            'query': 'artificial intelligence',
            'limit': 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)
        # First result should be document1 as it's more relevant
        self.assertEqual(response.data['results'][0]['document_id'], str(self.document1.id))

    def test_search_with_filters(self):
        """Test search with additional filters"""
        url = reverse('search')
        data = {
            'query': 'machine learning',
            'limit': 10,
            'filters': {
                'document_type': 'text/plain'
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)

    def test_empty_query(self):
        """Test search with empty query"""
        url = reverse('search')
        data = {
            'query': '',
            'limit': 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        """Test unauthorized access to search"""
        self.client.credentials()  # Remove authentication
        url = reverse('search')
        data = {
            'query': 'test',
            'limit': 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test search respects organization boundaries"""
        # Create another org with its own document
        other_org = Organization.objects.create(name='Other Org')
        other_doc = Document.objects.create(
            name='other.txt',
            content_type='text/plain',
            organization=other_org,
            status='COMPLETED',
            content='Secret information from other organization'
        )
        
        url = reverse('search')
        data = {
            'query': 'secret information',
            'limit': 10
        }
        response = self.client.post(url, data, format='json')
        
        # Verify other org's document is not in results
        result_ids = [r['document_id'] for r in response.data['results']]
        self.assertNotIn(str(other_doc.id), result_ids)

    def test_search_pagination(self):
        """Test search results pagination"""
        url = reverse('search')
        data = {
            'query': 'test',
            'limit': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue('next_cursor' in response.data)
