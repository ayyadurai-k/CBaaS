from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.test.utils import override_settings
from django.db.models import F
from apps.organizations.models import Organization
from apps.documents.models import Document, DocumentChunk
from apps.users.models import User
from apps.api_keys.models import APIKey
from common.llm.embeddings import get_embedding
import numpy as np

class SearchViewTests(APITestCase):
    """Test cases for SearchView"""
    
    def setUp(self):
        """Set up test data"""
        # Create organization
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
        
        # Create test documents with chunks
        self.setup_test_documents()
        
        # Set up authentication
        self.client.force_authenticate(user=self.user)
        
        # URL for search endpoint
        self.url = reverse('search')
        
        # Test query data
        self.query_data = {
            'query': 'artificial intelligence and machine learning',
            'top_k': 5,
            'filters': {}
        }

    def setup_test_documents(self):
        """Set up test documents and chunks with embeddings"""
        # Document 1: AI focused
        self.doc1 = Document.objects.create(
            name='ai_guide.pdf',
            file_type='pdf',
            organization=self.organization,
            uploaded_by=self.user,
            status=Document.Status.PROCESSED
        )
        
        # Create chunks for doc1
        chunk1_1 = DocumentChunk.objects.create(
            document=self.doc1,
            chunk_index=0,
            content='Artificial Intelligence (AI) is transforming industries.',
            embedding=self.create_mock_embedding(0.9)  # High relevance to AI
        )
        
        chunk1_2 = DocumentChunk.objects.create(
            document=self.doc1,
            chunk_index=1,
            content='Deep learning is a subset of machine learning.',
            embedding=self.create_mock_embedding(0.8)
        )
        
        # Document 2: ML focused
        self.doc2 = Document.objects.create(
            name='ml_basics.txt',
            file_type='txt',
            organization=self.organization,
            uploaded_by=self.user,
            status=Document.Status.PROCESSED
        )
        
        chunk2_1 = DocumentChunk.objects.create(
            document=self.doc2,
            chunk_index=0,
            content='Machine learning algorithms learn from data.',
            embedding=self.create_mock_embedding(0.85)
        )
        
        # Document 3: Unrelated
        self.doc3 = Document.objects.create(
            name='web_dev.pdf',
            file_type='pdf',
            organization=self.organization,
            uploaded_by=self.user,
            status=Document.Status.PROCESSED
        )
        
        chunk3_1 = DocumentChunk.objects.create(
            document=self.doc3,
            chunk_index=0,
            content='Web development basics and best practices.',
            embedding=self.create_mock_embedding(0.2)  # Low relevance
        )
        
        self.all_docs = [self.doc1, self.doc2, self.doc3]
        self.all_chunks = [chunk1_1, chunk1_2, chunk2_1, chunk3_1]

    def create_mock_embedding(self, similarity_factor):
        """Create a mock embedding vector with controlled similarity"""
        base_vector = np.random.rand(1536)
        noise = np.random.rand(1536) * (1 - similarity_factor)
        vector = base_vector * similarity_factor + noise
        return (vector / np.linalg.norm(vector)).tolist()

    def test_search_basic_functionality(self):
        """Test basic search functionality with similarity ranking"""
        mock_query_embedding = self.create_mock_embedding(1.0)
        
        with patch('apps.search.views.get_embedding', return_value=mock_query_embedding):
            response = self.client.post(self.url, self.query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('results', response.data)
            results = response.data['results']
            
            # Verify results structure and ordering
            self.assertTrue(len(results) > 0)
            self.assertTrue(all(r['score'] >= 0 and r['score'] <= 1 for r in results))
            self.assertEqual(results, sorted(results, key=lambda x: x['score'], reverse=True))
            
            # Verify result fields
            first_result = results[0]
            self.assertIn('document_id', first_result)
            self.assertIn('chunk_index', first_result)
            self.assertIn('content', first_result)
            self.assertIn('score', first_result)

    def test_search_with_filters(self):
        """Test search with various filter combinations"""
        mock_embedding = self.create_mock_embedding(1.0)
        
        with patch('apps.search.views.get_embedding', return_value=mock_embedding):
            # Test document_ids filter
            query_data = {**self.query_data}
            query_data['filters'] = {
                'document_ids': [str(self.doc1.id)]
            }
            response = self.client.post(self.url, query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(all(r['document_id'] == str(self.doc1.id) 
                              for r in response.data['results']))
            
            # Test file_types filter
            query_data['filters'] = {
                'file_types': ['pdf']
            }
            response = self.client.post(self.url, query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            pdf_doc_ids = [str(doc.id) for doc in [self.doc1, self.doc3]]
            self.assertTrue(all(r['document_id'] in pdf_doc_ids 
                              for r in response.data['results']))
            
            # Test combined filters
            query_data['filters'] = {
                'document_ids': [str(self.doc1.id), str(self.doc2.id)],
                'file_types': ['pdf']
            }
            response = self.client.post(self.url, query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(all(r['document_id'] == str(self.doc1.id) 
                              for r in response.data['results']))

    def test_search_authentication_and_authorization(self):
        """Test search endpoint authentication and authorization"""
        # Test without authentication
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.query_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with API key authentication
        self.client.credentials(HTTP_X_API_KEY=self.api_key.key)
        mock_embedding = self.create_mock_embedding(1.0)
        with patch('apps.search.views.get_embedding', return_value=mock_embedding):
            response = self.client.post(self.url, self.query_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify API key usage count increment
            self.api_key.refresh_from_db()
            self.assertEqual(self.api_key.usage_count, 1)
        
        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url, self.query_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_organization_isolation(self):
        """Test search results are isolated between organizations"""
        # Create another organization with documents
        other_org = Organization.objects.create(name='Other Org')
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            organization=other_org
        )
        
        other_doc = Document.objects.create(
            name='other_ai.pdf',
            file_type='pdf',
            organization=other_org,
            uploaded_by=other_user,
            status=Document.Status.PROCESSED
        )
        
        DocumentChunk.objects.create(
            document=other_doc,
            chunk_index=0,
            content='Confidential AI research results.',
            embedding=self.create_mock_embedding(0.95)  # High relevance
        )
        
        # Test with original user
        mock_embedding = self.create_mock_embedding(1.0)
        with patch('apps.search.views.get_embedding', return_value=mock_embedding):
            response = self.client.post(self.url, self.query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            result_doc_ids = [r['document_id'] for r in response.data['results']]
            self.assertNotIn(str(other_doc.id), result_doc_ids)
            
            # Test with other organization's user
            self.client.force_authenticate(user=other_user)
            response = self.client.post(self.url, self.query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            result_doc_ids = [r['document_id'] for r in response.data['results']]
            self.assertNotIn(str(self.doc1.id), result_doc_ids)
            self.assertNotIn(str(self.doc2.id), result_doc_ids)
            self.assertIn(str(other_doc.id), result_doc_ids)

    def test_search_input_validation(self):
        """Test search input validation"""
        invalid_cases = [
            # Empty query
            {
                'query': '',
                'top_k': 5
            },
            # Missing query
            {
                'top_k': 5
            },
            # Invalid top_k
            {
                'query': 'test',
                'top_k': -1
            },
            # Invalid filters format
            {
                'query': 'test',
                'top_k': 5,
                'filters': 'invalid'
            },
            # Invalid document_ids
            {
                'query': 'test',
                'top_k': 5,
                'filters': {
                    'document_ids': ['invalid-id']
                }
            }
        ]
        
        for data in invalid_cases:
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_error_handling(self):
        """Test search error handling"""
        # Test embedding service error
        with patch('apps.search.views.get_embedding', 
                  side_effect=Exception('Embedding service error')):
            response = self.client.post(self.url, self.query_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Test database query error
        with patch('apps.search.views.DocumentChunk.objects.filter', 
                  side_effect=Exception('Database error')):
            response = self.client.post(self.url, self.query_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_RATES': {'search': '2/minute'}})
    def test_search_rate_limiting(self):
        """Test search rate limiting"""
        mock_embedding = self.create_mock_embedding(1.0)
        
        with patch('apps.search.views.get_embedding', return_value=mock_embedding):
            # Make requests up to limit
            for _ in range(2):
                response = self.client.post(self.url, self.query_data, format='json')
                self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # This request should be throttled
            response = self.client.post(self.url, self.query_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_search_performance(self):
        """Test search performance with larger result sets"""
        # Create many document chunks
        bulk_chunks = []
        for i in range(100):
            bulk_chunks.append(DocumentChunk(
                document=self.doc1,
                chunk_index=i + 10,
                content=f'Content chunk {i}',
                embedding=self.create_mock_embedding(0.5)
            ))
        DocumentChunk.objects.bulk_create(bulk_chunks)
        
        mock_embedding = self.create_mock_embedding(1.0)
        with patch('apps.search.views.get_embedding', return_value=mock_embedding):
            # Test with different top_k values
            for top_k in [5, 20, 50]:
                query_data = {**self.query_data, 'top_k': top_k}
                response = self.client.post(self.url, query_data, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(response.data['results']), top_k)

    def test_search_empty_results(self):
        """Test search with no matching results"""
        # Delete all chunks
        DocumentChunk.objects.all().delete()
        
        mock_embedding = self.create_mock_embedding(1.0)
        with patch('apps.search.views.get_embedding', return_value=mock_embedding):
            response = self.client.post(self.url, self.query_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 0)
        
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
