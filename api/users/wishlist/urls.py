from django.urls import path
from .views import WishlistCreateAPIView, WishlistListAPIView, WishlistDeleteAPIView

urlpatterns = [
    path("create/", WishlistCreateAPIView.as_view(), name="wishlist_create"),
    path("list/", WishlistListAPIView.as_view(), name="wishlist_list"),
    path("detail/<uuid:product_id>/", WishlistDeleteAPIView.as_view(), name="wishlist_delete"),
]