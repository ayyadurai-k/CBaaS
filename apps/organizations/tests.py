from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.organizations.models import Organization
from rest_framework_simplejwt.tokens import RefreshToken

class OrganizationTests(APITestCase):
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

    def test_update_organization(self):
        """Test updating organization details"""
        url = reverse('organization-detail')
        data = {
            'name': 'Updated Org Name',
            'settings': {'theme': 'dark'}
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, 'Updated Org Name')
        self.assertEqual(self.organization.settings['theme'], 'dark')

    def test_delete_organization(self):
        """Test deleting organization"""
        url = reverse('organization-detail')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Organization.objects.count(), 0)

    def test_unauthorized_access(self):
        """Test unauthorized access to organization endpoints"""
        self.client.credentials()  # Remove authentication
        url = reverse('organization-detail')
        response = self.client.put(url, {'name': 'New Name'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_organization_access(self):
        """Test accessing wrong organization"""
        other_org = Organization.objects.create(name='Other Org')
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            organization=other_org
        )
        
        # Login as other user
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('organization-detail')
        data = {'name': 'Hacked Name'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify original org wasn't changed
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, 'Test Org')
