from django.urls import path
from .views import ProfileView

urlpatterns = [path("user/profile", ProfileView.as_view())]
