from django.db import transaction
from rest_framework import serializers

from apps.orders.models.address import Address


class AddressReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "region",
            "city",
            "street",
            "house",
            "apartment",
            "note",
            "is_default",
            "created_at",
            "updated_at",
        ]


class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "label",
            "region",
            "city",
            "street",
            "house",
            "apartment",
            "note",
            "is_default",
        ]

    def validate_street(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Street is required.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        is_default = validated_data.get("is_default", False)

        if is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)

        return Address.objects.create(user=user, **validated_data)


class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "label",
            "region",
            "city",
            "street",
            "house",
            "apartment",
            "note",
            "is_default",
        ]
        extra_kwargs = {
            "label": {"required": False},
            "region": {"required": False},
            "city": {"required": False},
            "street": {"required": False},
            "house": {"required": False},
            "apartment": {"required": False},
            "note": {"required": False},
            "is_default": {"required": False},
        }

    def validate_street(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Street cannot be empty.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        is_default = validated_data.get("is_default", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if is_default is True:
            Address.objects.filter(
                user=instance.user,
                is_default=True,
            ).exclude(id=instance.id).update(is_default=False)

        instance.save()
        return instance