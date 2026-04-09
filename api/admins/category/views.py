# GET /api/v1/categories/
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.admins.category.serializers import AdminCategoryListSerializer, CategoryCreateSerializer, \
    CategoryUpdateSerializer
from apps.catalog.models.category import Category
from common.permissions.worker_permission import IsWorker


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [IsWorker | IsAdminUser]

    def get_serializer_class(self):
        if self.action == "create":
            return CategoryCreateSerializer
        if self.action in ["update", "partial_update"]:
            return CategoryUpdateSerializer
        return AdminCategoryListSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.products.exists():
            return Response(
                {
                    "detail": "Avval shu kategoriyaga tegishli mahsulotlarni boshqa kategoriyaga o‘tkazing yoki o‘chiring."},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(
            {"detail": "Kategoriya muvaffaqiyatli o‘chirildi."},
            status=status.HTTP_204_NO_CONTENT
        )
