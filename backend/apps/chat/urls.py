from django.urls import path
from .views import ChatCompletionsView, ChatStreamView

urlpatterns = [
    path("chat/completions", ChatCompletionsView.as_view()),
    path("chat/stream", ChatStreamView.as_view()),
]
