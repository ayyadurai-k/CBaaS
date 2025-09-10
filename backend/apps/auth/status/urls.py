from django.urls import path

from .views import AuthStatusView

urlpatterns = [
    path("auth/status/", AuthStatusView.as_view(), name="auth_status"),
]
