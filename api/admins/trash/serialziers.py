from rest_framework import serializers

from apps.catalog.models.product import Product


class RestoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = []