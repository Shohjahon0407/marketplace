from rest_framework.routers import DefaultRouter

from api.admins.orders.views import AdminOrderViewSet

router = DefaultRouter()
router.register("order", AdminOrderViewSet, basename="admin-order")

urlpatterns = router.urls