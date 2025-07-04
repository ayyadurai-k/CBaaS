from django.urls import path
from apps.auth.logout.views import hello_world

urlpatterns = [
    path('hello/', hello_world, name='hello_world'),
]