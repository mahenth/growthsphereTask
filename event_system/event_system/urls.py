from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# This is the security configuration for Swagger to handle JWT tokens.
# It defines an API key type of "Bearer", which is the standard for JWTs.
security_definitions = {
    'Bearer': {
        'type': 'apiKey',
        'name': 'Authorization',
        'in': 'header'
    }
}

# This sets the security scheme for all operations, making all endpoints require a token.
security_requirements = [{'Bearer': []}]

schema_view = get_schema_view(
    openapi.Info(
        title="Event Scheduling API",
        default_version="v1",
        description="API for Event Scheduling & Reservation System",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    # Add the security configuration to the schema view.
    security_definitions=security_definitions,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Include app urls
    path("api/", include("events.urls")),

    # JWT authentication
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Swagger documentation
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc-ui"),
]