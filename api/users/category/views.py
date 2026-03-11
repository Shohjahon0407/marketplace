# GET /api/v1/categories/
from rest_framework.generics import ListAPIView

from api.users.category.serializers import CategoryListSerializer
from apps.catalog.models.category import Category


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
