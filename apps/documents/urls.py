from django.urls import path

from apps.documents.views import (
    DocumentDetailView,
    DocumentListCreateView,
    DocumentReprocessView,
)

urlpatterns = [
    path("documents", DocumentListCreateView.as_view()),
    path("documents/<uuid:pk>", DocumentDetailView.as_view()),
    path("documents/<uuid:pk>/reprocess", DocumentReprocessView.as_view()),
]
