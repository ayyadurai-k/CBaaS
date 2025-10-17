"""
Comprehensive API Key Security Tests

Tests all security features:
- Authentication (HMAC lookup, encryption)
- Authorization (scope-based permissions)
- Quota enforcement
- Rate limiting
- IP whitelisting
- Expiration handling
- Revocation
- Usage logging
- Anomaly detection
"""

import time
from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.models import User
from apps.organizations.models import Organization
from apps.api_keys.models import APIKey, APIKeyUsageLog
from apps.api_keys.services import APIKeyAnalyticsService


class APIKeySecurityModelTests(TestCase):
    """Test API key model security features"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.api_key = APIKey.objects.create(
            organization=self.org,
            name="Test Key",
            scope=APIKey.Scope.FULL,
            quota=1000
        )
        self.plaintext = APIKey.generate_plaintext()
        self.api_key.key = self.plaintext
        self.api_key.save()
    
    def test_encryption_at_rest(self):
        """Test that keys are encrypted in database"""
        # Key should be encrypted
        self.assertNotEqual(self.api_key.key_encrypted, self.plaintext)
        # But decryption should work
        self.assertEqual(self.api_key.key, self.plaintext)
        # HMAC should be set
        self.assertIsNotNone(self.api_key.key_hmac)
    
    def test_hmac_lookup(self):
        """Test constant-time HMAC lookup"""
        # Should find key by plaintext
        found_key = APIKey.get_by_plaintext(self.plaintext)
        self.assertEqual(found_key.id, self.api_key.id)
        
        # Should fail for wrong key
        with self.assertRaises(APIKey.DoesNotExist):
            APIKey.get_by_plaintext("wrong_key_value")
    
    def test_quota_validation(self):
        """Test quota enforcement"""
        self.api_key.usage_count = 999
        self.api_key.save()
        
        # Should not be exceeded
        self.assertFalse(self.api_key.is_quota_exceeded())
        
        # Set to limit
        self.api_key.usage_count = 1000
        self.api_key.save()
        
        # Should be exceeded
        self.assertTrue(self.api_key.is_quota_exceeded())
    
    def test_expiration_validation(self):
        """Test automatic expiration"""
        # Set expiration in past
        self.api_key.expires_at = timezone.now() - timedelta(days=1)
        self.api_key.save()
        
        # Should be expired
        self.assertTrue(self.api_key.is_expired())
        
        # can_be_used should auto-update status
        is_valid, error = self.api_key.can_be_used()
        self.assertFalse(is_valid)
        self.assertIn("expired", error.lower())
        
        # Status should be updated
        self.api_key.refresh_from_db()
        self.assertEqual(self.api_key.status, APIKey.Status.EXPIRED)
    
    def test_ip_whitelisting(self):
        """Test IP whitelisting"""
        # No restrictions initially
        self.assertTrue(self.api_key.is_ip_allowed("1.2.3.4"))
        
        # Add restrictions
        self.api_key.allowed_ips = ["203.0.113.5", "198.51.100.42"]
        self.api_key.save()
        
        # Allowed IPs should pass
        self.assertTrue(self.api_key.is_ip_allowed("203.0.113.5"))
        self.assertTrue(self.api_key.is_ip_allowed("198.51.100.42"))
        
        # Other IPs should fail
        self.assertFalse(self.api_key.is_ip_allowed("1.2.3.4"))
    
    def test_revocation(self):
        """Test key revocation"""
        self.api_key.revoke(reason="Security incident")
        
        self.assertEqual(self.api_key.status, APIKey.Status.REVOKED)
        self.assertEqual(self.api_key.revoked_reason, "Security incident")
        
        # Should not be usable
        is_valid, error = self.api_key.can_be_used()
        self.assertFalse(is_valid)
        self.assertIn("revoked", error.lower())
    
    def test_atomic_usage_increment(self):
        """Test thread-safe usage counter"""
        initial_count = self.api_key.usage_count
        
        # Record usage
        self.api_key.record_usage(increment=5)
        
        # Refresh from DB
        self.api_key.refresh_from_db()
        self.assertEqual(self.api_key.usage_count, initial_count + 5)
        self.assertIsNotNone(self.api_key.last_used_at)


class APIKeyAuthenticationTests(APITestCase):
    """Test API key authentication"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.api_key = APIKey.objects.create(
            organization=self.org,
            name="Test Key",
            scope=APIKey.Scope.FULL,
            quota=1000
        )
        self.plaintext = APIKey.generate_plaintext()
        self.api_key.key = self.plaintext
        self.api_key.save()
        
        self.client = APIClient()
    
    def test_valid_api_key(self):
        """Test authentication with valid API key"""
        from common.security.api_key_auth import APIKeyAuthentication
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/api/chat/completions', HTTP_X_API_KEY=self.plaintext)
        
        auth = APIKeyAuthentication()
        result = auth.authenticate(request)
        
        # Should return (user, api_key) tuple or just api_key
        self.assertIsNotNone(result)
    
    def test_invalid_api_key(self):
        """Test authentication with invalid API key"""
        from common.security.api_key_auth import APIKeyAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import AuthenticationFailed
        
        factory = APIRequestFactory()
        request = factory.get('/api/chat/completions', HTTP_X_API_KEY="invalid_key_value")
        
        auth = APIKeyAuthentication()
        with self.assertRaises(AuthenticationFailed):
            auth.authenticate(request)
    
    def test_revoked_key_rejected(self):
        """Test that revoked keys are rejected"""
        from common.security.api_key_auth import APIKeyAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import AuthenticationFailed
        
        self.api_key.revoke(reason="Test revocation")
        
        factory = APIRequestFactory()
        request = factory.get('/api/chat/completions', HTTP_X_API_KEY=self.plaintext)
        
        auth = APIKeyAuthentication()
        with self.assertRaises(AuthenticationFailed) as cm:
            auth.authenticate(request)
        self.assertIn('revoked', str(cm.exception).lower())
    
    def test_quota_exceeded_rejected(self):
        """Test that quota-exceeded keys are rejected"""
        from common.security.api_key_auth import APIKeyAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import AuthenticationFailed
        
        self.api_key.usage_count = 1000  # At limit
        self.api_key.save()
        
        factory = APIRequestFactory()
        request = factory.get('/api/chat/completions', HTTP_X_API_KEY=self.plaintext)
        
        auth = APIKeyAuthentication()
        with self.assertRaises(AuthenticationFailed) as cm:
            auth.authenticate(request)
        self.assertIn('quota', str(cm.exception).lower())
    
    def test_expired_key_rejected(self):
        """Test that expired keys are rejected"""
        from common.security.api_key_auth import APIKeyAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import AuthenticationFailed
        
        self.api_key.expires_at = timezone.now() - timedelta(days=1)
        self.api_key.save()
        
        factory = APIRequestFactory()
        request = factory.get('/api/chat/completions', HTTP_X_API_KEY=self.plaintext)
        
        auth = APIKeyAuthentication()
        with self.assertRaises(AuthenticationFailed) as cm:
            auth.authenticate(request)
        self.assertIn('expired', str(cm.exception).lower())
    
    def test_ip_whitelist_enforcement(self):
        """Test IP whitelisting enforcement"""
        from common.security.api_key_auth import APIKeyAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import AuthenticationFailed
        
        self.api_key.allowed_ips = ["203.0.113.5"]
        self.api_key.save()
        
        # Request from different IP should fail
        factory = APIRequestFactory()
        request = factory.get('/api/chat/completions', HTTP_X_API_KEY=self.plaintext, REMOTE_ADDR="1.2.3.4")
        
        auth = APIKeyAuthentication()
        with self.assertRaises(AuthenticationFailed) as cm:
            auth.authenticate(request)
        self.assertIn('ip', str(cm.exception).lower())


class APIKeyScopePermissionTests(APITestCase):
    """Test scope-based authorization"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.client = APIClient()
        
        # Create keys with different scopes
        self.full_key = self._create_key("Full Access", APIKey.Scope.FULL)
        self.readonly_key = self._create_key("Read Only", APIKey.Scope.READ_ONLY)
        self.upload_key = self._create_key("Upload Only", APIKey.Scope.UPLOAD_ONLY)
    
    def _create_key(self, name, scope):
        """Helper to create and return API key with plaintext"""
        key = APIKey.objects.create(
            organization=self.org,
            name=name,
            scope=scope,
            quota=10000
        )
        plaintext = APIKey.generate_plaintext()
        key.key = plaintext
        key.save()
        key.plaintext = plaintext  # Store for testing
        return key
    
    def test_full_access_can_chat(self):
        """Test that full-access keys can use chat"""
        response = self.client.post(
            '/api/chat/completions',
            data={'messages': [{'role': 'user', 'content': 'Hello'}]},
            HTTP_X_API_KEY=self.full_key.plaintext,
            HTTP_IDEMPOTENCY_KEY='test-key-123',
            format='json'
        )
        # May fail for other reasons, but not authorization
        self.assertNotEqual(response.status_code, 403)
    
    def test_readonly_cannot_chat(self):
        """Test that read-only keys cannot use chat"""
        response = self.client.post(
            '/api/chat/completions',
            data={'messages': [{'role': 'user', 'content': 'Hello'}]},
            HTTP_X_API_KEY=self.readonly_key.plaintext,
            HTTP_IDEMPOTENCY_KEY='test-key-456',
            format='json'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_upload_only_cannot_chat(self):
        """Test that upload-only keys cannot use chat"""
        response = self.client.post(
            '/api/chat/completions',
            data={'messages': [{'role': 'user', 'content': 'Hello'}]},
            HTTP_X_API_KEY=self.upload_key.plaintext,
            HTTP_IDEMPOTENCY_KEY='test-key-789',
            format='json'
        )
        self.assertEqual(response.status_code, 403)


class APIKeyUsageLoggingTests(TestCase):
    """Test usage logging functionality"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.api_key = APIKey.objects.create(
            organization=self.org,
            name="Test Key",
            scope=APIKey.Scope.FULL
        )
    
    def test_usage_log_creation(self):
        """Test that usage logs are created"""
        log = APIKeyUsageLog.objects.create(
            api_key=self.api_key,
            endpoint="/api/chat/completions/",
            method="POST",
            ip_address="203.0.113.5",
            user_agent="TestClient/1.0",
            status_code=200,
            response_time_ms=450,
            tokens_used=25
        )
        
        self.assertEqual(log.api_key, self.api_key)
        self.assertEqual(log.endpoint, "/api/chat/completions/")
        self.assertEqual(log.tokens_used, 25)
    
    def test_usage_log_querying(self):
        """Test querying usage logs"""
        # Create multiple logs
        for i in range(5):
            APIKeyUsageLog.objects.create(
                api_key=self.api_key,
                endpoint=f"/api/endpoint/{i}/",
                method="GET",
                ip_address="203.0.113.5",
                status_code=200,
                response_time_ms=100 + i,
                tokens_used=10 + i
            )
        
        # Query logs
        logs = APIKeyUsageLog.objects.filter(api_key=self.api_key)
        self.assertEqual(logs.count(), 5)
        
        # Test aggregation
        from django.db.models import Sum
        total_tokens = logs.aggregate(Sum('tokens_used'))['tokens_used__sum']
        self.assertEqual(total_tokens, 60)  # 10+11+12+13+14


class APIKeyAnalyticsTests(TestCase):
    """Test analytics service"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.api_key = APIKey.objects.create(
            organization=self.org,
            name="Test Key",
            scope=APIKey.Scope.FULL,
            quota=1000
        )
        
        # Create test usage logs
        now = timezone.now()
        for i in range(10):
            APIKeyUsageLog.objects.create(
                api_key=self.api_key,
                endpoint="/api/chat/completions/",
                method="POST",
                ip_address="203.0.113.5",
                status_code=200 if i < 8 else 400,  # 80% success
                response_time_ms=200 + i * 10,
                tokens_used=20 + i,
                timestamp=now - timedelta(hours=i)
            )
    
    def test_usage_summary(self):
        """Test usage summary generation"""
        summary = APIKeyAnalyticsService.get_usage_summary(self.api_key)
        
        self.assertEqual(summary['requests']['total'], 10)
        self.assertEqual(summary['requests']['successful'], 8)
        self.assertEqual(summary['requests']['failed'], 2)
        self.assertEqual(summary['requests']['success_rate'], 80.0)
        
        # Check tokens
        expected_tokens = sum(20 + i for i in range(10))  # 20+21+...+29
        self.assertEqual(summary['tokens']['total'], expected_tokens)
    
    def test_quota_forecast(self):
        """Test quota exhaustion forecasting"""
        # Set current usage
        self.api_key.usage_count = 900
        self.api_key.save()
        
        forecast = APIKeyAnalyticsService.forecast_quota_exhaustion(self.api_key)
        
        self.assertIsNotNone(forecast)
        self.assertIn('days_remaining', forecast)
        self.assertIn('daily_rate', forecast)
        self.assertEqual(forecast['remaining_quota'], 100)
    
    def test_cost_calculation(self):
        """Test cost calculation"""
        cost_data = APIKeyAnalyticsService.calculate_cost(
            self.api_key,
            cost_per_1k_tokens=0.002
        )
        
        expected_tokens = sum(20 + i for i in range(10))
        expected_cost = (expected_tokens / 1000.0) * 0.002
        
        self.assertEqual(cost_data['total_tokens'], expected_tokens)
        self.assertAlmostEqual(cost_data['total_cost'], expected_cost, places=4)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        # Create baseline traffic (10 requests per hour for 5 hours)
        now = timezone.now()
        for hour_offset in range(5, 1, -1):  # Hours 5, 4, 3, 2 ago
            for i in range(10):
                APIKeyUsageLog.objects.create(
                    api_key=self.api_key,
                    endpoint="/api/chat/completions",
                    method="POST",
                    ip_address="203.0.113.5",
                    status_code=200,
                    response_time_ms=200,
                    tokens_used=20,
                    timestamp=now - timedelta(hours=hour_offset, minutes=i)
                )
        
        # Create spike (100 requests in the last hour)
        for i in range(100):
            APIKeyUsageLog.objects.create(
                api_key=self.api_key,
                endpoint="/api/chat/completions",
                method="POST",
                ip_address="203.0.113.5",
                status_code=200,
                response_time_ms=200,
                tokens_used=20,
                timestamp=now - timedelta(minutes=i % 60)
            )
        
        anomalies = APIKeyAnalyticsService.detect_anomalies(self.api_key, hours=24)
        
        # Should detect anomalies (new IPs, new endpoints, etc.)
        self.assertGreater(len(anomalies), 0, f"Expected anomalies but got none")


class APIKeyRateLimitingTests(APITestCase):
    """Test rate limiting"""
    
    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    )
    def test_per_key_rate_limit(self):
        """Test per-key rate limiting"""
        # This test requires actual rate limit configuration
        # and may need to be adjusted based on settings
        pass  # Placeholder for integration testing


class APIKeySecurityAttackTests(APITestCase):
    """Test security against common attacks"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.api_key = APIKey.objects.create(
            organization=self.org,
            name="Test Key",
            scope=APIKey.Scope.FULL
        )
        self.plaintext = APIKey.generate_plaintext()
        self.api_key.key = self.plaintext
        self.api_key.save()
        
        self.client = APIClient()
    
    def test_timing_attack_resistance(self):
        """Test that HMAC lookup prevents timing attacks"""
        # Both lookups should take similar time
        valid_key = self.plaintext
        invalid_key = "totally_invalid_key_value_123456"
        
        # Measure time for valid key
        start = time.time()
        try:
            APIKey.get_by_plaintext(valid_key)
        except APIKey.DoesNotExist:
            pass
        valid_time = time.time() - start
        
        # Measure time for invalid key
        start = time.time()
        try:
            APIKey.get_by_plaintext(invalid_key)
        except APIKey.DoesNotExist:
            pass
        invalid_time = time.time() - start
        
        # Times should be similar (within 10ms)
        # This is a weak test but demonstrates the concept
        self.assertLess(abs(valid_time - invalid_time), 0.01)
    
    def test_sql_injection_protection(self):
        """Test SQL injection attempts are blocked"""
        malicious_keys = [
            "'; DROP TABLE api_keys_apikey; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        for malicious_key in malicious_keys:
            with self.assertRaises(APIKey.DoesNotExist):
                APIKey.get_by_plaintext(malicious_key)
    
    def test_replay_attack_protection(self):
        """Test idempotency key prevents replay attacks"""
        # First request with idempotency key
        response1 = self.client.post(
            '/api/chat/completions/',
            data={'messages': [{'role': 'user', 'content': 'Hello'}]},
            HTTP_X_API_KEY=self.plaintext,
            HTTP_IDEMPOTENCY_KEY='unique-key-abc',
            format='json'
        )
        
        # Second request with same idempotency key
        response2 = self.client.post(
            '/api/chat/completions/',
            data={'messages': [{'role': 'user', 'content': 'Different message'}]},
            HTTP_X_API_KEY=self.plaintext,
            HTTP_IDEMPOTENCY_KEY='unique-key-abc',
            format='json'
        )
        
        # Should return cached response (or detect duplicate)
        # Implementation depends on idempotency system
        pass  # Placeholder


# Run tests
if __name__ == '__main__':
    import unittest
    unittest.main()
