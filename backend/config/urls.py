from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from apps.core.views import HealthCheckView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


urlpatterns = [
    path("api/health/", HealthCheckView.as_view(), name="health_check"),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    path("admin/", admin.site.urls),

    # Auth
    path("api/auth/", include("apps.accounts.urls")),

    # JWT helpers
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/auth/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify",
    ),

    # App APIs
    path("api/searches/", include("apps.searches.urls")),
    path("api/leads/", include("apps.leads.urls")),
    path("api/usage/", include("apps.usage.urls")),
    path("api/admin-dashboard/", include("apps.admin_dashboard.urls")),
    path("api/monitoring/", include("apps.monitoring.urls")),
    path("api/ai/", include("apps.ai.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)