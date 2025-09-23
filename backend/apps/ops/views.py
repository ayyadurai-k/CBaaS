from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.db import connections
from django.conf import settings

from apps.chatbot.models import Chatbot
from common.services.logging_service import logging_service, log_api_call, log_performance

import redis
from celery import current_app

class HealthzView(APIView):
    permission_classes = [AllowAny]

    @log_api_call(view_name="health_check")
    def get(self, request):
        """Health check endpoint - basic service availability."""
        db_status = "ok"
        redis_status = "ok"

        # Check DB connection with performance logging
        try:
            @log_performance("db_health_check")
            def check_db():
                with connections["default"].cursor() as cursor:
                    cursor.execute("SELECT 1")
            
            check_db()
            logging_service.log_business_event(
                event_type="health_check",
                message="Database health check passed",
                request_id=getattr(request, 'request_id', None),
                component="db"
            )
        except Exception as e:
            db_status = "failed"
            logging_service.log_error(
                error=e,
                message="Database health check failed",
                request=request,
                component="db"
            )

        # Check Redis connection with performance logging
        try:
            @log_performance("redis_health_check")
            def check_redis():
                redis_instance = redis.from_url(settings.CELERY_BROKER_URL)
                redis_instance.ping()
            
            check_redis()
            logging_service.log_business_event(
                event_type="health_check",
                message="Redis health check passed",
                request_id=getattr(request, 'request_id', None),
                component="redis"
            )
        except Exception as e:
            redis_status = "failed"
            logging_service.log_error(
                error=e,
                message="Redis health check failed",
                request=request,
                component="redis"
            )

        # Log overall health status
        overall_status = "healthy" if db_status == "ok" and redis_status == "ok" else "unhealthy"
        logging_service.log_business_event(
            event_type="health_check_result",
            message=f"Health check completed: {overall_status}",
            request_id=getattr(request, 'request_id', None),
            db_status=db_status,
            redis_status=redis_status,
            overall_status=overall_status
        )

        return Response({"db": db_status, "redis": redis_status}, status=status.HTTP_200_OK)


class ReadyzView(APIView):
    permission_classes = [AllowAny]

    @log_api_call(view_name="readiness_check")
    def get(self, request):
        """Readiness check endpoint - full service readiness including dependencies."""
        db_status = "ok"
        redis_status = "ok"
        celery_status = "ok"
        provider_status = "missing"

        # Check DB connection
        try:
            @log_performance("db_readiness_check")
            def check_db():
                with connections["default"].cursor() as cursor:
                    cursor.execute("SELECT 1")
            
            check_db()
            logging_service.log_business_event(
                event_type="readiness_check",
                message="Database readiness check passed",
                request_id=getattr(request, 'request_id', None),
                component="db"
            )
        except Exception as e:
            db_status = "failed"
            logging_service.log_error(
                error=e,
                message="Database readiness check failed",
                request=request,
                component="db"
            )

        # Check Redis connection
        try:
            @log_performance("redis_readiness_check")
            def check_redis():
                redis_instance = redis.from_url(settings.CELERY_BROKER_URL)
                redis_instance.ping()
            
            check_redis()
            logging_service.log_business_event(
                event_type="readiness_check",
                message="Redis readiness check passed",
                request_id=getattr(request, 'request_id', None),
                component="redis"
            )
        except Exception as e:
            redis_status = "failed"
            logging_service.log_error(
                error=e,
                message="Redis readiness check failed",
                request=request,
                component="redis"
            )

        # Check Celery
        try:
            @log_performance("celery_readiness_check")
            def check_celery():
                # This will send a ping task to a worker and wait for a response
                # It requires a worker to be running and able to process tasks
                result = current_app.control.ping(timeout=1, destination=['celery@%h'])
                if not result or not result[0].get('celery@%h') == 'pong':
                    raise Exception("Celery worker not responding")
            
            check_celery()
            logging_service.log_business_event(
                event_type="readiness_check",
                message="Celery readiness check passed",
                request_id=getattr(request, 'request_id', None),
                component="celery"
            )
        except Exception as e:
            celery_status = "failed"
            logging_service.log_error(
                error=e,
                message="Celery readiness check failed",
                request=request,
                component="celery"
            )

        # Check if any ChatbotProvider exists
        try:
            @log_performance("provider_readiness_check")
            def check_provider():
                if Chatbot.objects.exists():
                    return "configured"
                return "missing"
            
            provider_status = check_provider()
            logging_service.log_business_event(
                event_type="readiness_check",
                message=f"Provider readiness check: {provider_status}",
                request_id=getattr(request, 'request_id', None),
                component="provider",
                provider_status=provider_status
            )
        except Exception as e:
            logging_service.log_error(
                error=e,
                message="Provider readiness check failed",
                request=request,
                component="provider"
            )

        # Log overall readiness status
        overall_status = "ready" if all(s == "ok" for s in [db_status, redis_status, celery_status]) and provider_status == "configured" else "not_ready"
        logging_service.log_business_event(
            event_type="readiness_check_result",
            message=f"Readiness check completed: {overall_status}",
            request_id=getattr(request, 'request_id', None),
            db_status=db_status,
            redis_status=redis_status,
            celery_status=celery_status,
            provider_status=provider_status,
            overall_status=overall_status
        )

        return Response({
            "db": db_status,
            "redis": redis_status,
            "celery": celery_status,
            "provider": provider_status
        }, status=status.HTTP_200_OK)
