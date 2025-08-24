from django.urls import path

from apps.organizations.views import OrganizationView

urlpatterns = [
    path("user/organization", OrganizationView.as_view()),
]
