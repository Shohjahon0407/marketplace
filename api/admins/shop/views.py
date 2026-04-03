from rest_framework.viewsets import ModelViewSet

from apps.shop.models import Shop
from api.admins.shop.serializers import (
    ShopDetailListSerializer,
    ShopDetailCreateSerializer,
    ShopDetailUpdateSerializer,
)


class ShopDetails(ModelViewSet):
    queryset = Shop.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return ShopDetailListSerializer
        elif self.action == 'create':
            return ShopDetailCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ShopDetailUpdateSerializer
        return ShopDetailListSerializer
