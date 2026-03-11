# GET /api/v1/products/
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from api.users.product.serializers import ProductListSerializer
from apps.catalog.models.product import Product
from utils.filters.category_filter import ProductFilter


class ProductListAPIView(ListAPIView):
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter