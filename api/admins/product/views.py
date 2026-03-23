from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from api.admins.product.serializers import ProductCreateSerializer, ProductReadSerializer, ProductUpdateSerializer
from apps.catalog.models.product import Product
from common.permissions.worker_permission import IsWorker
from utils.filters.category_filter import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "detail").prefetch_related("images")
    parser_classes = (MultiPartParser, FormParser)
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    permission_classes = [IsWorker or IsAdminUser ]

    def get_serializer_class(self):
        if self.action == "create":
            return ProductCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProductUpdateSerializer
        return ProductReadSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_200_OK)
