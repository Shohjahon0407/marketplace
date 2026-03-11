from django.urls import path

from .views import CartCreateAPIView, AddProductToCartAPIView, CartItemUpdateDeleteAPIView, CartDetailAPIView

urlpatterns = [
    path("cart/", CartCreateAPIView.as_view(), name="cart-create"),
    path("cart/add/", AddProductToCartAPIView.as_view(), name="cart-add-product"),
    path("cart/items/<uuid:pk>/", CartItemUpdateDeleteAPIView.as_view(), name="cart-item-update-delete"),
    path("cart/items/", CartDetailAPIView.as_view(), name="cart-detail"),
]
