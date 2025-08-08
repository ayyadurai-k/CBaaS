from rest_framework.filters import BaseFilterBackend

class OrganizationFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        org = getattr(request, "organization", None) or getattr(request.user, "organization", None)
        if org is None:
            return queryset.none()
        model = queryset.model
        if hasattr(model, "organization_id"):
            return queryset.filter(organization=org)
        return queryset