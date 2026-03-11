from rest_framework.routers import DefaultRouter
from api.admins.trash.views import DeletedProducts

router = DefaultRouter()
router.register(r'admin/product', DeletedProducts, basename='admin-product')

urlpatterns = router.urls
