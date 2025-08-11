from django.urls import path

from apps.chatbot_provider.views import ChatbotProviderUpsertView, TestKeyView

urlpatterns = [
    path("chatbot/test-key", TestKeyView.as_view()),
    path("chatbot/provider", ChatbotProviderUpsertView.as_view()), 
]
