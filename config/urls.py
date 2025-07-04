"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api_keys/', include('apps.api_keys.urls')),
    path('auth/login/', include('apps.auth.login.urls')),
    path('auth/logout/', include('apps.auth.logout.urls')),
    path('auth/reset/', include('apps.auth.reset.urls')),
    path('auth/signup/', include('apps.auth.signup.urls')),
    path('chatbot/', include('apps.chatbot.urls')),
    path('chatbot_provider/', include('apps.chatbot_provider.urls')),
    path('documents/', include('apps.documents.urls')),
    path('organizations/', include('apps.organizations.urls')),
    path('users/', include('apps.users.urls')),
]
