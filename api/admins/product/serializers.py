from django.db import transaction
from rest_framework import serializers

from apps.catalog.models.product import Product, ProductCount, ProductImage, Status


class ProductImageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductCreateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(write_only=True, min_value=0)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "discount_price",
            "quantity",
            "sku",
            "status",
        ]
        read_only_fields = ["id", "sku", "status"]

    def validate_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        uploaded_images = request.FILES.getlist("images") if request else []

        category = attrs.get("category")
        name = attrs.get("name")
        price = attrs.get("price")
        discount_price = attrs.get("discount_price")
        quantity = attrs.get("quantity")

        if price is None or price <= 0:
            raise serializers.ValidationError({
                "price": "Price must be greater than 0."
            })

        if discount_price is not None:
            if discount_price < 0:
                raise serializers.ValidationError({
                    "discount_price": "Discount price cannot be negative."
                })
            if discount_price >= price:
                raise serializers.ValidationError({
                    "discount_price": "Discount price must be less than price."
                })

        if quantity is None or quantity < 0:
            raise serializers.ValidationError({
                "quantity": "Quantity must be 0 or greater."
            })

        if len(uploaded_images) > 10:
            raise serializers.ValidationError({
                "images": "You can upload at most 10 images."
            })

        exists = Product.all_objects.filter(
            category=category,
            name__iexact=name
        ).exists()
        if exists:
            raise serializers.ValidationError({
                "name": "This product already exists in this category."
            })

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        uploaded_images = request.FILES.getlist("images")

        quantity = validated_data.pop("quantity")
        validated_data["status"] = (
            Status.OUT_OF_STOCK if quantity == 0 else Status.IN_STOCK
        )

        with transaction.atomic():
            product = Product.objects.create(**validated_data)

            ProductCount.objects.create(
                product=product,
                stock=quantity
            )

            if uploaded_images:
                ProductImage.objects.bulk_create([
                    ProductImage(product=product, image=image)
                    for image in uploaded_images
                ])

        return product


class ProductCountReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCount
        fields = ["stock"]


class ProductReadSerializer(serializers.ModelSerializer):
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
            "status",
            "sku",
            "detail",
            "images",
            "created_at",
            "updated_at",
        ]


class ProductUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(write_only=True, required=False, min_value=0)
    images = serializers.ImageField(write_only=True, required=False)
    delete_image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    replace_images = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "discount_price",
            "quantity",
            "images",
            "delete_image_ids",
            "replace_images",
            "sku",
            "status",
        ]
        read_only_fields = ["id", "sku", "status"]
        extra_kwargs = {
            "category": {"required": False},
            "name": {"required": False},
            "description": {"required": False},
            "price": {"required": False},
            "discount_price": {"required": False},
        }

    def validate_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        images = request.FILES.getlist("images") if request else []

        category = attrs.get("category", self.instance.category)
        name = attrs.get("name", self.instance.name)
        price = attrs.get("price", self.instance.price)
        discount_price = attrs.get("discount_price", self.instance.discount_price)
        quantity = attrs.get("quantity", self.instance.detail.stock)
        delete_image_ids = attrs.get("delete_image_ids", [])

        if price is not None and price <= 0:
            raise serializers.ValidationError({
                "price": "Price must be greater than 0."
            })

        if discount_price is not None:
            if discount_price < 0:
                raise serializers.ValidationError({
                    "discount_price": "Discount price cannot be negative."
                })
            if discount_price >= price:
                raise serializers.ValidationError({
                    "discount_price": "Discount price must be less than price."
                })

        if quantity is not None and quantity < 0:
            raise serializers.ValidationError({
                "quantity": "Quantity must be 0 or greater."
            })

        exists = Product.all_objects.filter(
            category=category,
            name__iexact=name
        ).exclude(pk=self.instance.pk).exists()

        if exists:
            raise serializers.ValidationError({
                "name": "This product already exists in this category."
            })

        if len(images) > 10:
            raise serializers.ValidationError({
                "images": "You can upload at most 10 images at once."
            })

        if delete_image_ids:
            valid_ids = set(self.instance.images.values_list("id", flat=True))
            invalid_ids = set(delete_image_ids) - valid_ids
            if invalid_ids:
                raise serializers.ValidationError({
                    "delete_image_ids": f"These image IDs do not belong to this product: {list(invalid_ids)}"
                })

        return attrs

    def update(self, instance, validated_data):
        request = self.context["request"]
        images = request.FILES.getlist("images")
        validated_data.pop("images", None)

        quantity = validated_data.pop("quantity", None)
        delete_image_ids = validated_data.pop("delete_image_ids", [])
        replace_images = validated_data.pop("replace_images", False)

        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)

            if quantity is not None:
                instance.status = (
                    Status.OUT_OF_STOCK if quantity == 0 else Status.IN_STOCK
                )

            instance.save()

            if quantity is not None:
                ProductCount.objects.update_or_create(
                    product=instance,
                    defaults={"stock": quantity}
                )

            if replace_images:
                instance.images.all().delete()
            elif delete_image_ids:
                instance.images.filter(id__in=delete_image_ids).delete()

            if images:
                ProductImage.objects.bulk_create([
                    ProductImage(product=instance, image=image)
                    for image in images
                ])

        return instance
