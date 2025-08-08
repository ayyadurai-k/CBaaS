from django.urls import path
from .views import TestKeyView, ChatbotProviderUpsertView

urlpatterns = [
    path("chatbot/test-key", TestKeyView.as_view()),
    path("chatbot/provider", ChatbotProviderUpsertView.as_view()),  # <-- new
]
