import re
from rest_framework import serializers


PHONE_REGEX = r'^\+998\d{9}$'


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13, min_length=13)

    def validate(self, attrs):
        phone = attrs.get("phone", "").strip()

        if not re.fullmatch(PHONE_REGEX, phone):
            raise serializers.ValidationError({
                "phone": "Telefon raqam +998901234567 formatida bo‘lishi kerak."
            })

        attrs["phone"] = phone
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13, min_length=13)
    code = serializers.CharField(max_length=5, min_length=5)

    def validate(self, attrs):
        phone = attrs.get("phone", "").strip()
        code = attrs.get("code", "").strip()

        if not re.fullmatch(PHONE_REGEX, phone):
            raise serializers.ValidationError({
                "phone": "Telefon raqam +998901234567 formatida bo‘lishi kerak."
            })

        if not code.isdigit():
            raise serializers.ValidationError({
                "code": "Kod faqat raqamlardan iborat bo‘lishi kerak."
            })

        attrs["phone"] = phone
        attrs["code"] = code
        return attrs


class PasswordLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13, min_length=13)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        phone = attrs.get("phone", "").strip()

        if not re.fullmatch(PHONE_REGEX, phone):
            raise serializers.ValidationError({
                "phone": "Telefon raqam +998901234567 formatida bo‘lishi kerak."
            })

        attrs["phone"] = phone
        return attrs