from django.urls import path

from apps.users.views import ProfileView

urlpatterns = [
    path("user/profile", ProfileView.as_view()),
]
