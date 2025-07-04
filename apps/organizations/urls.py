from django.urls import path
from apps.organizations.views import hello_world

urlpatterns = [
    path('hello/', hello_world, name='hello_world'),
]