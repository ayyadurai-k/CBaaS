from django.urls import path

from apps.chatbot.views import ChatbotView, TestApiKeyView, ChatbotMessageView

urlpatterns = [
    path("chatbot", ChatbotView.as_view(), name="chatbot-config"),
    path("chatbot/test-api-key", TestApiKeyView.as_view(), name="chatbot-test-api-key"),
    path("chatbot/message", ChatbotMessageView.as_view(), name="chatbot-message"),
]
