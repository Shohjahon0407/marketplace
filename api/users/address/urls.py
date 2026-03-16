from django.urls import path

from .views import (
    AddressListCreateAPIView,
    AddressDetailAPIView,
    DefaultAddressAPIView,
)

urlpatterns = [
    path("addresses/", AddressListCreateAPIView.as_view(), name="user-address-list-create"),
    path("addresses/default/", DefaultAddressAPIView.as_view(), name="user-address-default"),
    path("addresses/<uuid:pk>/", AddressDetailAPIView.as_view(), name="user-address-detail"),
]