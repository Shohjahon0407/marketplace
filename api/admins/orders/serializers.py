from django.db import transaction
from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from common.enums.enums import OrderStatus, DeliveryMethod
from common.status_update.cancel import restore_order_items_to_stock


class AdminOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit_price",
            "quantity",
            "total_price",
        ]


class AdminOrderListSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_code",
            "customer",
            "status",
            "delivery_method",
            "subtotal",
            "delivery_fee",
            "total_price",
            "items_count",
            "created_at",
        ]

    def get_customer(self, obj):
        return str(obj.user)

    def get_items_count(self, obj):
        return obj.items.count()


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    items = AdminOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_code",
            "customer",
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
        ]

    def get_customer(self, obj):
        return str(obj.user)


class AdminOrderStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)

    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        order = self.instance
        current_status = order.status

        allowed_transitions = {
            OrderStatus.PENDING: {
                OrderStatus.CONFIRMED,
                OrderStatus.CANCELLED,
            },
            OrderStatus.CONFIRMED: {
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED,
            },
            OrderStatus.CANCELLED: set(),
            OrderStatus.DELIVERED: set(),
        }

        if value == current_status:
            return value

        if value not in allowed_transitions.get(current_status, set()):
            raise serializers.ValidationError(
                f"'{current_status}' statusdan '{value}' statusga o'tkazib bo'lmaydi."
            )

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


class AdminPickupByCodeSerializer(serializers.Serializer):
    order_code = serializers.CharField()

    def validate(self, attrs):
        order_code = attrs["order_code"].strip().upper()

        try:
            order = (
                Order.objects
                .select_related("user")
                .prefetch_related("items")
                .get(order_code=order_code, is_deleted=False)
            )
        except Order.DoesNotExist:
            raise serializers.ValidationError({
                "order_code": "Bunday order code topilmadi."
            })

        if order.delivery_method != DeliveryMethod.PICKUP:
            raise serializers.ValidationError({
                "order_code": "Bu order pickup emas."
            })

        if order.status == OrderStatus.CANCELLED:
            raise serializers.ValidationError({
                "order_code": "Bu order cancelled qilingan."
            })

        if order.status == OrderStatus.DELIVERED:
            raise serializers.ValidationError({
                "order_code": "Bu order allaqachon topshirilgan."
            })

        attrs["order"] = order
        attrs["order_code"] = order_code
        return attrs

    def save(self, **kwargs):
        order = self.validated_data["order"]
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status", "updated_at"])
        return order
