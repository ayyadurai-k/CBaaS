from django.urls import path
from .views import APIKeyListCreateView, APIKeyRevokeView, APIKeyDeleteView

urlpatterns = [
    path("keys", APIKeyListCreateView.as_view()),
    path("keys/<uuid:pk>/revoke", APIKeyRevokeView.as_view()),
    path("keys/<uuid:pk>", APIKeyDeleteView.as_view()),
]