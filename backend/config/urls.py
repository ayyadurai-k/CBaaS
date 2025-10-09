from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    
    # Health/readiness endpoints
    path("api/", include("apps.ops.urls")), 
    

    # Auth flows
    path("api/", include("apps.auth.signup.urls")),
    path("api/", include("apps.auth.login.urls")),
    path("api/", include("apps.auth.logout.urls")),
    path("api/", include("apps.auth.reset.urls")),
    path("api/", include("apps.auth.status.urls")),

    # User/org
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.organizations.urls")),

    # Domain
    path("api/", include("apps.documents.urls")),
    path("api/", include("apps.chatbot.urls")),
    path("api/", include("apps.api_keys.urls")),
    path("api/", include("apps.search.urls")),
    path("api/", include("apps.chat.urls")),
]

# Serve static/media files based on SERVE_STATIC_FILES setting
# Development: Django serves files locally
# Production: S3 serves files (SERVE_STATIC_FILES=False)
if getattr(settings, 'SERVE_STATIC_FILES', False):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)