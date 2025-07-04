from django.urls import path
from apps.api_keys.views import hello_world

urlpatterns = [
    path('hello/', hello_world, name='hello_world'),
]