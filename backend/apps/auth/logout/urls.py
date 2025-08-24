from django.urls import path

from apps.auth.logout.views import LogoutView

urlpatterns = [
    path("auth/logout", LogoutView.as_view()),
]
