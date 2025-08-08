from django.urls import path
from .views import LogoutView

urlpatterns = [path("auth/logout", LogoutView.as_view())]
