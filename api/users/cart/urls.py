from django.urls import path

from .views import CartCreateAPIView, AddProductToCartAPIView, CartItemUpdateDeleteAPIView, CartDetailAPIView

urlpatterns = [
    path("create/", CartCreateAPIView.as_view(), name="cart-create"),
    path("add/", AddProductToCartAPIView.as_view(), name="cart-add-product"),
    path("items/<int:pk>/", CartItemUpdateDeleteAPIView.as_view(), name="cart-item-update-delete"),
    path("items/", CartDetailAPIView.as_view(), name="cart-detail"),
]
