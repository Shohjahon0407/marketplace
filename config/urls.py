from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


user_schema_view = get_schema_view(
    openapi.Info(
        title="Clinic API",
        default_version="v1",
        description="Marketplace backend API hujjatlari",
        contact=openapi.Contact(email="Marketplace.uz"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/v1/user/', include('api.users.urls')),
    ]
)

admin_schema_view = get_schema_view(
    openapi.Info(
        title="Clinic API",
        default_version="v1",
        description="Marketplace backend API hujjatlari",
        contact=openapi.Contact(email="dev@clinic.uz"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/v1/admin/', include('api.admins.urls')),
    ]
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('user/', include('api.users.urls')),
        path('admin/', include('api.admins.urls')),
        path('order_bot/', include('api.order_bot.urls')),

        path('bot/', include('api.bot.urls'))
    ])),
    path('swagger/', user_schema_view.with_ui('swagger', cache_timeout=0), name="swagger-ui"),
    path('swagger/admin/', admin_schema_view.with_ui('swagger', cache_timeout=0), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
