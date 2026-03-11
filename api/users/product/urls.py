from django.urls import path

from api.users.product.views import ProductListAPIView

urlpatterns = [
    path('product-list/', ProductListAPIView.as_view())

]