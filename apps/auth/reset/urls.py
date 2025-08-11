from django.urls import path

from apps.auth.reset.views import ForgotView, ResetView, VerifyView

urlpatterns = [
    path("auth/forgot-password", ForgotView.as_view()),
    path("auth/verify-reset-token", VerifyView.as_view()),
    path("auth/reset-password", ResetView.as_view()),
]
