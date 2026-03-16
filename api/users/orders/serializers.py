from decimal import Decimal
from django.db import transaction
from rest_framework import serializers

from apps.cart.models import Cart
from apps.catalog.models.product import ProductCount
from apps.orders.models.address import Address
from apps.orders.models.order import Order, OrderItem

from common.enums.enums import OrderStatus, DeliveryMethod
from common.status_update.cancel import restore_order_items_to_stock


def get_product_sell_price(product):
    return product.discount_price if product.discount_price is not None else product.price


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "unit_price",
            "quantity",
            "total_price",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "delivery_method",
            "delivery_fee",
            "subtotal",
            "total_price",
            "comment",
            "items_count",
            "created_at",
            "order_code",
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "delivery_method",
            "delivery_address",
            "delivery_fee",
            "subtotal",
            "total_price",
            "comment",
            "items",
            "created_at",
            "updated_at",
            "order_code",
        ]


class OrderCreateSerializer(serializers.Serializer):
    delivery_method = serializers.ChoiceField(choices=DeliveryMethod.choices)
    address_id = serializers.UUIDField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        try:
            cart = user.cart
        except Cart.DoesNotExist:
            raise serializers.ValidationError({"cart": "Foydalanuvchi carti topilmadi."})

        cart_items = cart.items.select_related("product", "product__detail")
        if not cart_items.exists():
            raise serializers.ValidationError({"cart": "Cart bo‘sh."})

        delivery_method = attrs.get("delivery_method")
        address_id = attrs.get("address_id")

        if delivery_method == DeliveryMethod.COURIER and not address_id:
            raise serializers.ValidationError({
                "address_id": "Courier delivery uchun address_id yuborilishi shart."
            })

        if address_id:
            if not Address.objects.filter(id=address_id, user=user, is_deleted=False).exists():
                raise serializers.ValidationError({
                    "address_id": "Address topilmadi yoki sizga tegishli emas."
                })

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        delivery_method = validated_data["delivery_method"]
        address_id = validated_data.get("address_id")
        comment = validated_data.get("comment", "")

        with transaction.atomic():
            cart = (
                Cart.objects
                .select_for_update()
                .select_related("user")
                .prefetch_related("items__product", "items__product__detail")
                .get(user_id=user.id)
            )

            cart_items = list(cart.items.all())
            if not cart_items:
                raise serializers.ValidationError({"cart": "Cart bo‘sh."})

            address_text = ""
            delivery_fee = Decimal("0.00")

            if delivery_method == DeliveryMethod.COURIER:
                address = Address.objects.get(id=address_id, user=user, is_deleted=False)
                address_text = (
                    f"{address.label}, {address.region}, {address.city}, "
                    f"{address.street}, {address.house}, {address.apartment}. {address.note}"
                ).strip(", ").strip()

                delivery_fee = Decimal("30000.00")  # misol, keyin sozlaysan

            subtotal = Decimal("0.00")
            order_items_to_create = []
            stock_objects_to_update = []

            for cart_item in cart_items:
                product = cart_item.product
                quantity = cart_item.quantity

                try:
                    product_count = ProductCount.objects.select_for_update().get(product=product)
                except ProductCount.DoesNotExist:
                    raise serializers.ValidationError({
                        "stock": f"'{product.name}' uchun stock ma'lumoti topilmadi."
                    })

                if product_count.stock < quantity:
                    raise serializers.ValidationError({
                        "stock": f"'{product.name}' uchun yetarli qoldiq yo‘q. Mavjud: {product_count.stock}"
                    })

                unit_price = get_product_sell_price(product)
                line_total = unit_price * quantity
                subtotal += line_total

                order_items_to_create.append(
                    OrderItem(
                        order=None,  # order keyin biriktiriladi
                        product=product,
                        product_name=product.name,
                        unit_price=unit_price,
                        quantity=quantity,
                        total_price=line_total,
                    )
                )

                product_count.stock -= quantity
                stock_objects_to_update.append(product_count)

            total_price = subtotal + delivery_fee

            order = Order.objects.create(
                user=user,
                status=OrderStatus.PENDING,
                delivery_method=delivery_method,
                delivery_address=address_text,
                delivery_fee=delivery_fee,
                subtotal=subtotal,
                total_price=total_price,
                comment=comment,
            )

            for item in order_items_to_create:
                item.order = order

            OrderItem.objects.bulk_create(order_items_to_create)
            ProductCount.objects.bulk_update(stock_objects_to_update, ["stock"])

            cart.items.all().delete()

        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)

    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        order = self.instance

        allowed_statuses = [OrderStatus.CANCELLED]
        if value not in allowed_statuses:
            raise serializers.ValidationError("User faqat orderni cancel qila oladi.")

        if order.status not in [OrderStatus.PENDING]:
            raise serializers.ValidationError("Faqat pending order cancel qilinadi.")

        return value

    def update(self, instance, validated_data):
        new_status = validated_data["status"]
        old_status = instance.status

        with transaction.atomic():
            if (
                    new_status == OrderStatus.CANCELLED
                    and old_status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
            ):
                restore_order_items_to_stock(instance)

            instance.status = new_status
            instance.save(update_fields=["status", "updated_at"])
            return instance
