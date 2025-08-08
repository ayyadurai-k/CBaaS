from django.urls import path
from .views import OrganizationView

urlpatterns = [path("user/organization", OrganizationView.as_view())]
