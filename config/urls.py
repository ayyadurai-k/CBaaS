from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),

    # Auth flows
    path("api/", include("apps.auth.signup.urls")),
    path("api/", include("apps.auth.login.urls")),
    path("api/", include("apps.auth.logout.urls")),
    path("api/", include("apps.auth.reset.urls")),

    # User/org
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.organizations.urls")),

    # Domain
    path("api/", include("apps.documents.urls")),
    path("api/", include("apps.chatbot.urls")),
    path("api/", include("apps.chatbot_provider.urls")),
    path("api/", include("apps.api_keys.urls")),
]