from rest_framework import serializers

from apps.catalog.models.category import Category


class AdminCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def validate(self, attrs):
        name = attrs.get('name', '').strip()
        description = attrs.get('description', '').strip()

        # Validate name is not empty after stripping
        if not name:
            raise serializers.ValidationError({"name": "Name cannot be blank or whitespace."})

        # Validate minimum name length
        if len(name) < 2:
            raise serializers.ValidationError({"name": "Name must be at least 2 characters long."})

        # Validate uniqueness (case-insensitive)
        qs = Category.objects.filter(name__iexact=name)
        if self.instance:  # exclude current instance on update
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({"name": "A category with this name already exists."})

        # Validate description length (optional field)
        if description and len(description) > 500:
            raise serializers.ValidationError({"description": "Description cannot exceed 500 characters."})

        # Normalize casing before saving
        attrs['name'] = name.title()
        attrs['description'] = description

        return attrs


class CategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']

    def validate(self, attrs):
        name = attrs.get('name', '').strip()
        description = attrs.get('description', '').strip()

        # Support partial updates (PATCH) — only validate name if provided
        if 'name' in attrs:
            if not name:
                raise serializers.ValidationError({"name": "Name cannot be blank or whitespace."})

            if len(name) < 2:
                raise serializers.ValidationError({"name": "Name must be at least 3 characters long."})

            # Case-insensitive uniqueness, excluding the current instance
            qs = Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"name": "A category with this name already exists."})

            attrs['name'] = name.title()

        # Only validate description if provided
        if 'description' in attrs:
            if description and len(description) > 500:
                raise serializers.ValidationError({"description": "Description cannot exceed 500 characters."})

            attrs['description'] = description

        return attrs
