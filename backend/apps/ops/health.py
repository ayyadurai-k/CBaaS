from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint for AWS ALB health checks.
    Returns basic system status without database dependency.
    """
    try:
        return JsonResponse({
            "status": "healthy",
            "service": "cbaas-backend",
            "timestamp": "2025-10-05T01:10:00Z"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e)
        }, status=500)