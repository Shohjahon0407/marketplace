from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.admins.product.serializers import ProductReadSerializer
from api.admins.trash.serialziers import RestoreSerializer
from apps.catalog.models.product import Product


class DeletedProducts(ModelViewSet):
    queryset = Product.all_objects.filter(is_deleted=True)
    http_method_names = ["get", "patch", "delete"]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action == "partial_update":
            return RestoreSerializer
        return ProductReadSerializer

    def partial_update(self, request, *args, **kwargs):
        product = self.get_object()

        if not product.is_deleted:
            return Response(
                {"detail": "Product is already active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product.restore()

        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()

        try:
            product.hard_delete()
        except ProtectedError:
            return Response(
                {
                    "detail": "Bu mahsulot oldingi buyurtmalarda ishlatilgan. Uni butunlay o‘chirib bo‘lmaydi."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Product permanently deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )