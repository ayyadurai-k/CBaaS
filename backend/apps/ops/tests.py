from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.db import OperationalError
from django.conf import settings
from apps.chatbot_provider.models import ChatbotProvider
import redis
import json

class HealthzViewTests(APITestCase):
    """Test cases for HealthzView"""

    def setUp(self):
        """Set up test data"""
        self.url = reverse("healthz")

    def test_healthz_success(self):
        """Test successful health check"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "ok")
        self.assertEqual(response.data["redis"], "ok")

    @patch('django.db.backends.base.base.BaseDatabaseWrapper.cursor')
    def test_healthz_db_failure(self, mock_cursor):
        """Test health check with database failure"""
        # Mock database error
        mock_cursor.side_effect = OperationalError("Could not connect to database")
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "failed")
        self.assertEqual(response.data["redis"], "ok")

    @patch('redis.from_url')
    def test_healthz_redis_failure(self, mock_redis):
        """Test health check with Redis failure"""
        # Mock Redis error
        mock_redis.return_value.ping.side_effect = redis.ConnectionError("Could not connect to Redis")
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "ok")
        self.assertEqual(response.data["redis"], "failed")

    @patch('django.db.backends.base.base.BaseDatabaseWrapper.cursor')
    @patch('redis.from_url')
    def test_healthz_all_failures(self, mock_redis, mock_cursor):
        """Test health check with all services failing"""
        # Mock both DB and Redis errors
        mock_cursor.side_effect = OperationalError("DB Error")
        mock_redis.return_value.ping.side_effect = redis.ConnectionError("Redis Error")
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "failed")
        self.assertEqual(response.data["redis"], "failed")

    def test_healthz_no_auth_required(self):
        """Test health check endpoint requires no authentication"""
        # Make request without any authentication
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ReadyzViewTests(APITestCase):
    """Test cases for ReadyzView"""

    def setUp(self):
        """Set up test data"""
        self.url = reverse("readyz")

    def test_readyz_success_no_provider(self):
        """Test successful readiness check without ChatbotProvider"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "ok")
        self.assertEqual(response.data["redis"], "ok")
        self.assertEqual(response.data["celery"], "ok")
        self.assertEqual(response.data["provider"], "missing")

    def test_readyz_success_with_provider(self):
        """Test successful readiness check with ChatbotProvider"""
        # Create a ChatbotProvider
        ChatbotProvider.objects.create(
            name="Test Provider",
            provider_type="openai",
            api_key="test-key",
            organization=None
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["provider"], "configured")

    @patch('django.db.backends.base.base.BaseDatabaseWrapper.cursor')
    def test_readyz_db_failure(self, mock_cursor):
        """Test readiness check with database failure"""
        mock_cursor.side_effect = OperationalError("DB Error")
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "failed")
        self.assertEqual(response.data["redis"], "ok")
        self.assertEqual(response.data["celery"], "ok")

    @patch('redis.from_url')
    def test_readyz_redis_failure(self, mock_redis):
        """Test readiness check with Redis failure"""
        mock_redis.return_value.ping.side_effect = redis.ConnectionError("Redis Error")
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "ok")
        self.assertEqual(response.data["redis"], "failed")
        self.assertEqual(response.data["celery"], "ok")

    @patch('celery.app.control.Control.ping')
    def test_readyz_celery_failure(self, mock_ping):
        """Test readiness check with Celery failure"""
        mock_ping.return_value = []  # Empty response indicates failure
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "ok")
        self.assertEqual(response.data["redis"], "ok")
        self.assertEqual(response.data["celery"], "failed")

    @patch('django.db.backends.base.base.BaseDatabaseWrapper.cursor')
    @patch('redis.from_url')
    @patch('celery.app.control.Control.ping')
    def test_readyz_all_failures(self, mock_ping, mock_redis, mock_cursor):
        """Test readiness check with all services failing"""
        # Mock all services failing
        mock_cursor.side_effect = OperationalError("DB Error")
        mock_redis.return_value.ping.side_effect = redis.ConnectionError("Redis Error")
        mock_ping.side_effect = Exception("Celery Error")
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["db"], "failed")
        self.assertEqual(response.data["redis"], "failed")
        self.assertEqual(response.data["celery"], "failed")
        self.assertEqual(response.data["provider"], "missing")

    def test_readyz_no_auth_required(self):
        """Test readiness check endpoint requires no authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_readyz_response_format(self):
        """Test readiness check response format"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_keys = {"db", "redis", "celery", "provider"}
        self.assertEqual(set(response.data.keys()), expected_keys)
        
        # Verify all values are strings
        for value in response.data.values():
            self.assertIsInstance(value, str)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    def test_readyz(self):
        """Test readiness check endpoint"""
        url = reverse('readyz')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        
        # Check component statuses
        self.assertIn('database', response.data['components'])
        self.assertIn('redis', response.data['components'])
        self.assertIn('celery', response.data['components'])
