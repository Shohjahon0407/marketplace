from rest_framework import serializers

from common.validators.phone_validator import phone_validator


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13, validators=[phone_validator])


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13, validators=[phone_validator])
    code = serializers.CharField(max_length=5, min_length=5)


class PasswordLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13, validators=[phone_validator])
    password = serializers.CharField(max_length=255)