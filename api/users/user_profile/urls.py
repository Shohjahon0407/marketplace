from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.users.user_profile.views import NewOrderListAPIView, AllOrdersListAPIView, ProfileViewSet

router = DefaultRouter()
router.register('', ProfileViewSet)

urlpatterns = [
    path('profile/', include(router.urls)),
    path('new-order/', NewOrderListAPIView.as_view()),
    path('all-orders', AllOrdersListAPIView.as_view()),

]
