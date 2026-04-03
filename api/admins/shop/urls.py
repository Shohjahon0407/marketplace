from rest_framework.routers import DefaultRouter

from api.admins.shop.views import ShopDetails

router = DefaultRouter()
router.register(r'shop-details', ShopDetails, basename='shop-details')

urlpatterns = router.urls