from django.urls import path
from apps.users.views import hello_world

urlpatterns = [
    path('hello/', hello_world, name='hello_world'),
]