from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.db import connections
from django.conf import settings

from apps.chatbot_provider.models import ChatbotProvider

import redis
from celery import current_app

class HealthzView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        db_status = "ok"
        redis_status = "ok"

        # Check DB connection
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_status = "failed"

        # Check Redis connection
        try:
            redis_instance = redis.from_url(settings.REDIS_URL)
            redis_instance.ping()
        except Exception:
            redis_status = "failed"

        return Response({"db": db_status, "redis": redis_status}, status=status.HTTP_200_OK)


class ReadyzView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        db_status = "ok"
        redis_status = "ok"
        celery_status = "ok"
        provider_status = "missing"

        # Check DB connection
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_status = "failed"

        # Check Redis connection
        try:
            redis_instance = redis.from_url(settings.REDIS_URL)
            redis_instance.ping()
        except Exception:
            redis_status = "failed"

        # Check Celery
        try:
            # This will send a ping task to a worker and wait for a response
            # It requires a worker to be running and able to process tasks
            result = current_app.control.ping(timeout=1, destination=['celery@%h'])
            if not result or not result[0].get('celery@%h') == 'pong':
                celery_status = "failed"
        except Exception:
            celery_status = "failed"

        # Check if any ChatbotProvider exists
        if ChatbotProvider.objects.exists():
            provider_status = "configured"

        return Response({
            "db": db_status,
            "redis": redis_status,
            "celery": celery_status,
            "provider": provider_status
        }, status=status.HTTP_200_OK)
