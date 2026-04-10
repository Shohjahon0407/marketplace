from rest_framework import serializers

from api.admins.product.serializers import ProductCountReadSerializer, ProductImageReadSerializer
from apps.catalog.models.category import Category
from apps.catalog.models.product import Product


class ProductListSerializer(serializers.ModelSerializer):
    detail = ProductCountReadSerializer(read_only=True)
    images = ProductImageReadSerializer(many=True, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "discount_price",
            "discount_percent",
            "bulk_price",
            "status",
            "detail",
            "images",
            "created_at",
        ]
