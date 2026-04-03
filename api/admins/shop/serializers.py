from rest_framework import serializers
from apps.shop.models import Shop


class ShopDetailListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'id',
            'shop_name',
            'order_fee',
            'shop_address',
        ]


class ShopDetailCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'shop_name',
            'order_fee',
            'shop_address',
        ]

    def validate(self, attrs):
        shop_name = attrs.get('shop_name', '').strip()
        order_fee = attrs.get('order_fee', 0)
        shop_address = attrs.get('shop_address', '')

        if len(shop_name) == 1:
            raise serializers.ValidationError({
                "shop_name": "Do'kon nomi 1 ta harfdan iborat bo'lishi mumkin emas."
            })

        if order_fee < 0:
            raise serializers.ValidationError({
                "order_fee": "Yetkazib berish to'lovi manfiy bo'lishi mumkin emas."
            })

        if shop_address and len(shop_address.strip()) < 3:
            raise serializers.ValidationError({
                "shop_address": "Do'kon manzili kamida 3 ta belgidan iborat bo'lishi kerak."
            })

        return attrs


class ShopDetailUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'shop_name',
            'order_fee',
            'shop_address',
        ]

    def validate(self, attrs):
        shop_name = attrs.get('shop_name')
        order_fee = attrs.get('order_fee')
        shop_address = attrs.get('shop_address')

        if shop_name is not None and len(shop_name.strip()) == 1:
            raise serializers.ValidationError({
                "shop_name": "Do'kon nomi 1 ta harfdan iborat bo'lishi mumkin emas."
            })

        if order_fee is not None and order_fee < 0:
            raise serializers.ValidationError({
                "order_fee": "Yetkazib berish to'lovi manfiy bo'lishi mumkin emas."
            })

        if shop_address is not None and shop_address.strip() and len(shop_address.strip()) < 3:
            raise serializers.ValidationError({
                "shop_address": "Do'kon manzili kamida 3 ta belgidan iborat bo'lishi kerak."
            })

        return attrs