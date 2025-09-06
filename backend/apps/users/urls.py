from django.urls import path

from apps.users.views import ProfileView, ProfilePictureUploadView

urlpatterns = [
    path("user/profile", ProfileView.as_view()),
    path("user/profile/picture", ProfilePictureUploadView.as_view()),
]
