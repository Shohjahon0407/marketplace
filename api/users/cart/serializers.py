from rest_framework import serializers

from apps.cart.models import Cart, CartItem
from apps.catalog.models.product import Product
from common.enums.enums import Status


class CartProductSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source="detail.stock", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "price",
            "discount_price",
            "status",
            "stock",
            "sku",
        ]


class CartItemReadSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
            "total_price",
        ]


class CartReadSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "subtotal",
            "items",
        ]


class AddProductToCartSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        product_id = attrs["product"]
        quantity = attrs["quantity"]

        try:
            product = Product.objects.select_related("detail").get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product": "Product not found."})

        if product.status != Status.IN_STOCK:
            raise serializers.ValidationError({"product": "Product is out of stock."})

        if not hasattr(product, "detail"):
            raise serializers.ValidationError({"product": "Product stock info not found."})

        if product.detail.stock < quantity:
            raise serializers.ValidationError(
                {"quantity": "Requested quantity exceeds available stock."}
            )

        attrs["product_obj"] = product
        return attrs


class CartItemUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ["quantity"]

    def validate(self, attrs):
        quantity = attrs.get("quantity")
        product = self.instance.product

        if product.is_deleted:
            raise serializers.ValidationError({
                "product": "This product is no longer available."
            })

        if product.status != Status.IN_STOCK:
            raise serializers.ValidationError({
                "product": "Product is out of stock."
            })

        if not hasattr(product, "detail"):
            raise serializers.ValidationError({
                "product": "Product stock information not found."
            })

        if quantity > product.detail.stock:
            raise serializers.ValidationError({
                "quantity": "Requested quantity exceeds available stock."
            })

        return attrs
