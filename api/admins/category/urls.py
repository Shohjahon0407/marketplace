from rest_framework.routers import DefaultRouter

from api.admins.category.views import CategoryViewSet

router = DefaultRouter()

router.register('', CategoryViewSet)


urlpatterns = router.urls

