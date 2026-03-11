from rest_framework.routers import DefaultRouter

from api.admins.product.views import ProductViewSet

router = DefaultRouter()

router.register('', ProductViewSet)


urlpatterns = router.urls

