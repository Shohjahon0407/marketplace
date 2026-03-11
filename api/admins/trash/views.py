from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.admins.product.serializers import ProductReadSerializer
from api.admins.trash.serialziers import RestoreSerializer
from apps.catalog.models.product import Product


class DeletedProducts(ModelViewSet):
    queryset = Product.all_objects.filter(is_deleted=True)
    http_method_names = ["get", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == ['patch']:
            return RestoreSerializer
        return ProductReadSerializer

    def partial_update(self, request, *args, **kwargs):
        product = self.get_object()

        if not product.is_deleted:
            return Response(
                {"detail": "Product is already active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.restore()

        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
