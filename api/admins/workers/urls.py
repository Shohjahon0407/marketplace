from rest_framework.routers import DefaultRouter

from api.admins.workers.views import WorkerCrud

router = DefaultRouter()
router.register('', WorkerCrud)

urlpatterns = router.urls
