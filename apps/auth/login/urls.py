from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.auth.login.views import LoginView

urlpatterns = [
    path("auth/login/", LoginView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
