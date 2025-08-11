from django.urls import path

from apps.api_keys.views import APIKeyDeleteView, APIKeyListCreateView, APIKeyRevokeView

urlpatterns = [
    path("keys", APIKeyListCreateView.as_view()),
    path("keys/<uuid:pk>/revoke", APIKeyRevokeView.as_view()),
    path("keys/<uuid:pk>", APIKeyDeleteView.as_view()),
]
