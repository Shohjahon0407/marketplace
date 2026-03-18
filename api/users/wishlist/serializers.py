from rest_framework import serializers
from apps.wishlist.models import Wishlist

class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    product_image = serializers.ImageField(source="product.image", read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product_name", "product_image", "added_at"]