# GET /api/v1/categories/
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet

from api.admins.category.serializers import AdminCategoryListSerializer, CategoryCreateSerializer, \
    CategoryUpdateSerializer
from apps.catalog.models.category import Category


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action == "create":
            return CategoryCreateSerializer
        if self.action in ["update", "partial_update"]:
            return CategoryUpdateSerializer
        return AdminCategoryListSerializer
