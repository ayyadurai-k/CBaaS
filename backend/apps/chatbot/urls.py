from django.urls import path

from apps.chatbot.views import ChatbotView

urlpatterns = [
    path("chatbot", ChatbotView.as_view()),
]
