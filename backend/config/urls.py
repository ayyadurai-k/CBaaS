from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
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

# CUSTOM STATIC FILE SERVING - Bypass Django's DEBUG check
# Django's static() function returns empty list when DEBUG=False
# We need to manually create the URL pattern for production static serving
if hasattr(settings, 'STATIC_URL') and hasattr(settings, 'STATIC_ROOT'):
    urlpatterns += [
        re_path(
            r'^static/(?P<path>.*)$', 
            serve, 
            {'document_root': settings.STATIC_ROOT}
        ),
    ]

if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT'):
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$', 
            serve, 
            {'document_root': settings.MEDIA_ROOT}
        ),
    ]