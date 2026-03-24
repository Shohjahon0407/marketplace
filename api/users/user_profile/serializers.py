from rest_framework import serializers

from apps.accounts.models import Profile

from apps.orders.models import Order

from rest_framework import serializers


class ProfileCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Profile
        fields = ["name", "gender", "birth_date"]

    def validate(self, attrs):
        birth_date = attrs.get("birth_date")
        request = self.context.get("request")
        user = request.user

        if Profile.objects.filter(user=user).exists():
            raise serializers.ValidationError("Sizda allaqachon profile bor")

        if not birth_date:
            raise serializers.ValidationError("Tug'ilgan kun bo'sh bo'lmasligi kerak")

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        name = validated_data.pop("name", None)

        if name is not None:
            user.name = name
            user.save()

        return Profile.objects.create(user=user, **validated_data)


class ProfileListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "user",
            "gender",
            "birth_date"
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = [
            "name",
            "gender",
            "birth_date",
        ]
        extra_kwargs = {
            "gender": {"required": False},
            "birth_date": {"required": False},
        }

    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)

        if name is not None:
            instance.user.name = name
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "order_code",
            "status",
            "delivery_method",
            "delivery_address",
            "delivery_fee",
            "subtotal",
            "total_price",
            "comment",
        ]
