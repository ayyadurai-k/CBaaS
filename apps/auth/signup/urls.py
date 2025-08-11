from django.urls import path

from apps.auth.signup.views import SignupView

urlpatterns = [
    path("auth/signup", SignupView.as_view()),
]
