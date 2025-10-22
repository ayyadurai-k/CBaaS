"""
Custom throttle classes for API rate limiting.

Implements both user-based and API-key-based throttling with
distributed rate limiting using Redis.
"""

import logging
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ChatRateThrottle(ScopedRateThrottle):
    """Rate throttle for chat endpoints"""
    scope = "chat"


class SearchRateThrottle(ScopedRateThrottle):
    """Rate throttle for search endpoints"""
    scope = "search"


class DocumentsRateThrottle(ScopedRateThrottle):
    """Rate throttle for document upload/management endpoints"""
    scope = "documents"


class APIKeyRateThrottle(SimpleRateThrottle):
    """
    Per-API-key rate throttle.
    
    Limits requests based on the individual API key, not the user or IP.
    Supports custom per-key rate limits that override the default.
    
    Rate limit precedence:
    1. API key's custom rate_limit_per_minute field
    2. Scope-based default from settings
    3. Global default
    """
    
    scope = 'api_key'
    
    def get_cache_key(self, request, view):
        """
        Generate unique cache key for this API key.
        Returns None if no API key authentication is used.
        """
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            # No API key auth, skip this throttle
            return None
        
        # Use API key ID as cache key
        return f'throttle_apikey_{api_key.id}'
    
    def get_rate(self):
        """
        Get the rate limit for the current request.
        
        Returns rate in format '60/min' or '1000/hour'
        """
        # Try to get API key from the request (set during allow_request)
        if hasattr(self, 'api_key') and self.api_key:
            # Check if this key has a custom rate limit
            if self.api_key.rate_limit_per_minute:
                return f'{self.api_key.rate_limit_per_minute}/min'
        
        # Fall back to scope-based rate from settings
        # Default: 60 requests per minute for API keys
        return '60/min'
    
    def allow_request(self, request, view):
        """
        Determine if the request should be allowed.
        
        Returns True if allowed, False if throttled.
        """
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            # No API key, allow (other throttles will apply)
            return True
        
        # Store API key for get_rate() method
        self.api_key = api_key
        
        # Use parent's rate limiting logic
        allowed = super().allow_request(request, view)
        
        if not allowed:
            logger.warning(
                f"API key rate limit exceeded",
                extra={
                    'api_key_id': str(api_key.id),
                    'api_key_name': api_key.name,
                    'rate_limit': self.get_rate(),
                    'path': request.path,
                    'method': request.method
                }
            )
        
        return allowed
    
    def wait(self):
        """
        Optionally, return a recommended number of seconds to wait before
        the next request.
        """
        return super().wait()


class BurstableAPIKeyThrottle(APIKeyRateThrottle):
    """
    Burstable rate throttle for API keys.
    
    Allows short bursts of traffic while maintaining overall rate limits.
    Uses two rate limits:
    - Burst: Short-term limit (e.g., 10/second)
    - Sustained: Long-term limit (e.g., 100/minute)
    """
    
    burst_scope = 'api_key_burst'
    sustained_scope = 'api_key_sustained'
    
    def allow_request(self, request, view):
        """
        Check both burst and sustained rate limits.
        Request is only allowed if both limits are satisfied.
        """
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return True
        
        self.api_key = api_key
        
        # Check burst limit (short-term)
        burst_key = f'throttle_burst_{api_key.id}'
        burst_history = cache.get(burst_key, [])
        burst_allowed = self._check_rate_limit(
            burst_history, burst_key, rate='10/sec'
        )
        
        # Check sustained limit (long-term)
        sustained_key = f'throttle_sustained_{api_key.id}'
        sustained_history = cache.get(sustained_key, [])
        sustained_allowed = self._check_rate_limit(
            sustained_history, sustained_key, rate=self.get_rate()
        )
        
        allowed = burst_allowed and sustained_allowed
        
        if not allowed:
            logger.warning(
                f"API key burst/sustained rate limit exceeded",
                extra={
                    'api_key_id': str(api_key.id),
                    'burst_allowed': burst_allowed,
                    'sustained_allowed': sustained_allowed,
                    'path': request.path
                }
            )
        
        return allowed
    
    def _check_rate_limit(self, history, cache_key, rate):
        """
        Internal helper to check a specific rate limit.
        
        Args:
            history: List of timestamps from cache
            cache_key: Redis cache key
            rate: Rate string like '10/sec' or '100/min'
        
        Returns:
            True if allowed, False if throttled
        """
        import time
        
        # Parse rate
        num_requests, period = self.parse_rate(rate)
        if num_requests is None:
            return True
        
        now = time.time()
        
        # Remove old entries outside the time window
        history = [t for t in history if t > now - period]
        
        # Check if we're under the limit
        if len(history) >= num_requests:
            return False
        
        # Add current request timestamp
        history.append(now)
        
        # Update cache
        cache.set(cache_key, history, timeout=int(period) + 10)
        
        return True
