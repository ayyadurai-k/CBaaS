from django.urls import path

from apps.organizations.views import OrganizationView, OrganizationLogoUploadView

urlpatterns = [
    path("user/organization", OrganizationView.as_view(), name="organization"),
    path("user/organization/logo", OrganizationLogoUploadView.as_view(), name="organization-logo"),
]
