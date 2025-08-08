from django.urls import path
from .views import TestKeyView

urlpatterns = [path("chatbot/test-key", TestKeyView.as_view())]
