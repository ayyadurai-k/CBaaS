from django.urls import path
from apps.ops.views import HealthzView, ReadyzView, StaticDebugView

urlpatterns = [
    path("healthz", HealthzView.as_view(), name="healthz"),
    path("readyz", ReadyzView.as_view(), name="readyz"),
    path("debug/static", StaticDebugView.as_view(), name="static_debug"),
]