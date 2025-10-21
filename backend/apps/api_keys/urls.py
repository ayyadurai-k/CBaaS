from django.urls import path

from apps.api_keys.views import (
    APIKeyDeleteView, 
    APIKeyListCreateView, 
    APIKeyRevokeView,
    APIKeyUpdateView
)

urlpatterns = [
    path("keys/", APIKeyListCreateView.as_view()),
    path("keys/<uuid:pk>/", APIKeyUpdateView.as_view()),
    path("keys/<uuid:pk>/revoke/", APIKeyRevokeView.as_view()),
    path("keys/<uuid:pk>/delete/", APIKeyDeleteView.as_view()),
]
