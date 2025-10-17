"""
API Key Analytics Service

Provides comprehensive analytics and insights for API key usage:
- Usage statistics (requests, tokens, errors)
- Quota tracking and forecasting
- Cost analysis and billing
- Anomaly detection
- Performance metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from apps.api_keys.models import APIKey, APIKeyUsageLog

logger = logging.getLogger(__name__)


class APIKeyAnalyticsService:
    """
    Service layer for API key analytics and reporting.
    
    Provides methods for:
    - Usage statistics
    - Quota forecasting
    - Cost calculation
    - Anomaly detection
    - Performance analysis
    """
    
    @classmethod
    def get_usage_summary(
        cls, 
        api_key: APIKey, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get comprehensive usage summary for an API key.
        
        Args:
            api_key: The API key to analyze
            start_date: Start of date range (default: 30 days ago)
            end_date: End of date range (default: now)
        
        Returns:
            Dictionary with usage statistics
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logs = APIKeyUsageLog.objects.filter(
            api_key=api_key,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Basic metrics
        total_requests = logs.count()
        successful_requests = logs.filter(status_code__lt=400).count()
        failed_requests = total_requests - successful_requests
        
        # Token usage
        token_stats = logs.aggregate(
            total_tokens=Sum('tokens_used'),
            avg_tokens_per_request=Avg('tokens_used')
        )
        
        # Performance metrics
        perf_stats = logs.aggregate(
            avg_response_time=Avg('response_time_ms'),
            min_response_time=Avg('response_time_ms'),
            max_response_time=Avg('response_time_ms')
        )
        
        # Endpoint breakdown
        endpoint_stats = list(
            logs.values('endpoint')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Error breakdown
        error_stats = list(
            logs.filter(status_code__gte=400)
            .values('status_code', 'error_message')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # IP addresses
        unique_ips = logs.values('ip_address').distinct().count()
        top_ips = list(
            logs.values('ip_address')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'requests': {
                'total': total_requests,
                'successful': successful_requests,
                'failed': failed_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0
            },
            'tokens': {
                'total': token_stats['total_tokens'] or 0,
                'avg_per_request': token_stats['avg_tokens_per_request'] or 0
            },
            'performance': {
                'avg_response_time_ms': perf_stats['avg_response_time'] or 0,
                'min_response_time_ms': perf_stats['min_response_time'] or 0,
                'max_response_time_ms': perf_stats['max_response_time'] or 0
            },
            'endpoints': endpoint_stats,
            'errors': error_stats,
            'ips': {
                'unique_count': unique_ips,
                'top': top_ips
            },
            'quota': {
                'current': api_key.usage_count,
                'limit': api_key.quota,
                'remaining': (api_key.quota - api_key.usage_count) if api_key.quota else None,
                'percentage_used': (api_key.usage_count / api_key.quota * 100) if api_key.quota else 0
            }
        }
    
    @classmethod
    def get_usage_timeline(
        cls,
        api_key: APIKey,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = 'day'
    ) -> List[Dict]:
        """
        Get time-series usage data for charting.
        
        Args:
            api_key: The API key
            start_date: Start date
            end_date: End date
            granularity: 'hour', 'day', or 'week'
        
        Returns:
            List of data points with timestamp and metrics
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            if granularity == 'hour':
                start_date = end_date - timedelta(hours=24)
            elif granularity == 'week':
                start_date = end_date - timedelta(weeks=12)
            else:  # day
                start_date = end_date - timedelta(days=30)
        
        # Determine date truncation
        from django.db.models.functions import TruncHour, TruncDay, TruncWeek
        
        trunc_funcs = {
            'hour': TruncHour,
            'day': TruncDay,
            'week': TruncWeek
        }
        trunc_func = trunc_funcs.get(granularity, TruncDay)
        
        # Aggregate by time period
        timeline = list(
            APIKeyUsageLog.objects.filter(
                api_key=api_key,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            .annotate(period=trunc_func('timestamp'))
            .values('period')
            .annotate(
                request_count=Count('id'),
                success_count=Count('id', filter=Q(status_code__lt=400)),
                error_count=Count('id', filter=Q(status_code__gte=400)),
                total_tokens=Sum('tokens_used'),
                avg_response_time=Avg('response_time_ms')
            )
            .order_by('period')
        )
        
        return [
            {
                'timestamp': item['period'].isoformat(),
                'requests': item['request_count'],
                'successes': item['success_count'],
                'errors': item['error_count'],
                'tokens': item['total_tokens'] or 0,
                'avg_response_time_ms': item['avg_response_time'] or 0
            }
            for item in timeline
        ]
    
    @classmethod
    def forecast_quota_exhaustion(cls, api_key: APIKey) -> Optional[Dict]:
        """
        Predict when quota will be exhausted based on recent usage.
        
        Args:
            api_key: The API key to analyze
        
        Returns:
            Forecast data or None if quota is unlimited
        """
        if not api_key.quota:
            return None
        
        # Get usage rate over last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        recent_requests = APIKeyUsageLog.objects.filter(
            api_key=api_key,
            timestamp__gte=week_ago
        ).count()
        
        if recent_requests == 0:
            return {
                'exhaustion_date': None,
                'days_remaining': None,
                'daily_rate': 0,
                'message': 'No recent usage'
            }
        
        # Calculate daily rate
        daily_rate = recent_requests / 7.0
        
        # Calculate remaining quota
        remaining = api_key.quota - api_key.usage_count
        
        if remaining <= 0:
            return {
                'exhaustion_date': timezone.now().isoformat(),
                'days_remaining': 0,
                'daily_rate': daily_rate,
                'message': 'Quota already exhausted'
            }
        
        # Forecast days until exhaustion
        days_remaining = remaining / daily_rate if daily_rate > 0 else float('inf')
        exhaustion_date = timezone.now() + timedelta(days=days_remaining)
        
        return {
            'exhaustion_date': exhaustion_date.isoformat() if days_remaining != float('inf') else None,
            'days_remaining': round(days_remaining, 1) if days_remaining != float('inf') else None,
            'daily_rate': round(daily_rate, 2),
            'weekly_rate': round(daily_rate * 7, 2),
            'remaining_quota': remaining,
            'current_usage': api_key.usage_count,
            'total_quota': api_key.quota,
            'message': cls._get_quota_message(days_remaining)
        }
    
    @classmethod
    def _get_quota_message(cls, days_remaining: float) -> str:
        """Generate human-readable quota status message"""
        if days_remaining == float('inf'):
            return 'Quota will not be exhausted at current rate'
        elif days_remaining < 1:
            return '⚠️ CRITICAL: Quota will be exhausted within 24 hours'
        elif days_remaining < 3:
            return '⚠️ WARNING: Quota will be exhausted within 3 days'
        elif days_remaining < 7:
            return 'ℹ️ Notice: Quota will be exhausted within a week'
        else:
            return f'✓ Quota sufficient for ~{int(days_remaining)} days'
    
    @classmethod
    def calculate_cost(
        cls,
        api_key: APIKey,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        cost_per_1k_tokens: float = 0.002
    ) -> Dict:
        """
        Calculate cost based on token usage.
        
        Args:
            api_key: The API key
            start_date: Start date
            end_date: End date
            cost_per_1k_tokens: Cost per 1000 tokens (default: $0.002)
        
        Returns:
            Cost breakdown
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logs = APIKeyUsageLog.objects.filter(
            api_key=api_key,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        total_tokens = logs.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
        total_cost = (total_tokens / 1000.0) * cost_per_1k_tokens
        
        # Cost per endpoint
        endpoint_costs = []
        for endpoint_data in logs.values('endpoint').annotate(tokens=Sum('tokens_used')):
            endpoint_tokens = endpoint_data['tokens']
            endpoint_cost = (endpoint_tokens / 1000.0) * cost_per_1k_tokens
            endpoint_costs.append({
                'endpoint': endpoint_data['endpoint'],
                'tokens': endpoint_tokens,
                'cost': round(endpoint_cost, 4)
            })
        
        endpoint_costs.sort(key=lambda x: x['cost'], reverse=True)
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 4),
            'cost_per_request': round(total_cost / logs.count(), 6) if logs.count() > 0 else 0,
            'breakdown_by_endpoint': endpoint_costs[:10],
            'pricing': {
                'cost_per_1k_tokens': cost_per_1k_tokens,
                'currency': 'USD'
            }
        }
    
    @classmethod
    def detect_anomalies(cls, api_key: APIKey, hours: int = 24) -> List[Dict]:
        """
        Detect unusual usage patterns.
        
        Args:
            api_key: The API key to analyze
            hours: Lookback period in hours
        
        Returns:
            List of detected anomalies
        """
        from django.db.models.functions import TruncHour
        
        anomalies = []
        cutoff = timezone.now() - timedelta(hours=hours)
        
        # Get recent logs
        recent_logs = APIKeyUsageLog.objects.filter(
            api_key=api_key,
            timestamp__gte=cutoff
        )
        
        # 1. Spike in requests
        hourly_counts = list(
            recent_logs.annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        if len(hourly_counts) >= 2:
            avg_per_hour = sum(h['count'] for h in hourly_counts) / len(hourly_counts)
            for hour_data in hourly_counts:
                if hour_data['count'] > avg_per_hour * 3:  # 3x average
                    anomalies.append({
                        'type': 'request_spike',
                        'severity': 'high',
                        'timestamp': hour_data['hour'],
                        'value': hour_data['count'],
                        'threshold': avg_per_hour * 3,
                        'message': f"Request spike: {hour_data['count']} requests (avg: {avg_per_hour:.1f})"
                    })
        
        # 2. High error rate
        total = recent_logs.count()
        errors = recent_logs.filter(status_code__gte=400).count()
        if total > 0:
            error_rate = (errors / total) * 100
            if error_rate > 10:  # >10% errors
                anomalies.append({
                    'type': 'high_error_rate',
                    'severity': 'medium',
                    'timestamp': timezone.now(),
                    'value': error_rate,
                    'threshold': 10,
                    'message': f"High error rate: {error_rate:.1f}% ({errors}/{total} requests)"
                })
        
        # 3. New IP addresses
        historical_ips = set(
            APIKeyUsageLog.objects.filter(
                api_key=api_key,
                timestamp__lt=cutoff
            ).values_list('ip_address', flat=True).distinct()
        )
        
        recent_ips = set(
            recent_logs.values_list('ip_address', flat=True).distinct()
        )
        
        new_ips = recent_ips - historical_ips
        if new_ips:
            anomalies.append({
                'type': 'new_ip_addresses',
                'severity': 'low',
                'timestamp': timezone.now(),
                'value': list(new_ips),
                'message': f"New IP addresses detected: {', '.join(new_ips)}"
            })
        
        # 4. Unusual endpoints
        common_endpoints = set(
            APIKeyUsageLog.objects.filter(
                api_key=api_key,
                timestamp__lt=cutoff
            ).values_list('endpoint', flat=True).distinct()
        )
        
        recent_endpoints = set(
            recent_logs.values_list('endpoint', flat=True).distinct()
        )
        
        new_endpoints = recent_endpoints - common_endpoints
        if new_endpoints:
            anomalies.append({
                'type': 'new_endpoints',
                'severity': 'low',
                'timestamp': timezone.now(),
                'value': list(new_endpoints),
                'message': f"New endpoints accessed: {', '.join(new_endpoints)}"
            })
        
        return anomalies
    
    @classmethod
    def compare_keys(cls, api_keys: List[APIKey], days: int = 30) -> Dict:
        """
        Compare performance across multiple API keys.
        
        Args:
            api_keys: List of API keys to compare
            days: Lookback period
        
        Returns:
            Comparison data
        """
        cutoff = timezone.now() - timedelta(days=days)
        
        comparison = []
        for key in api_keys:
            logs = APIKeyUsageLog.objects.filter(
                api_key=key,
                timestamp__gte=cutoff
            )
            
            stats = logs.aggregate(
                total_requests=Count('id'),
                total_tokens=Sum('tokens_used'),
                avg_response_time=Avg('response_time_ms'),
                error_count=Count('id', filter=Q(status_code__gte=400))
            )
            
            total = stats['total_requests'] or 1
            
            comparison.append({
                'id': str(key.id),
                'name': key.name,
                'scope': key.scope,
                'requests': stats['total_requests'],
                'tokens': stats['total_tokens'] or 0,
                'avg_response_time_ms': stats['avg_response_time'] or 0,
                'error_rate': (stats['error_count'] / total) * 100,
                'quota_usage': (key.usage_count / key.quota * 100) if key.quota else 0
            })
        
        return {
            'period_days': days,
            'keys': sorted(comparison, key=lambda x: x['requests'], reverse=True)
        }
