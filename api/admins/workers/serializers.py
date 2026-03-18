from rest_framework import serializers

from apps.accounts.models import User


class WorkerCreateSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'name',
            'phone',
            'email',
            'password',
            'confirm_password',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True},
        }

    def validate(self, attrs):
        password = attrs.get('password', '')
        confirm_password = attrs.get('confirm_password', '')
        errors = {}
        # Validate password and confirm_password
        if len(password) < 6:
            errors['password'] = "Parol kamida 6ta harfdan iborat bo'lishi kerak"
        if password != confirm_password:
            errors['confirm_password'] = "Parollar birxil bo'lishi kerak"

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_worker = True  # Assuming you want to mark them as a worker
        user.save()
        return user


class WorkerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id',
                  'name',
                  'phone',]


class WorkerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'name',
            'phone',
            'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
