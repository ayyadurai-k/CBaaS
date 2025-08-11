from django.urls import path

from apps.auth.login.views import LoginView

urlpatterns = [
    path("auth/login", LoginView.as_view()),
]
