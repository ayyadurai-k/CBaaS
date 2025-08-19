from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class OpsTests(APITestCase):
    def test_healthz(self):
        """Test health check endpoint"""
        url = reverse('healthz')
        response = self.client.get(url)
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
