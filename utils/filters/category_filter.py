from django_filters import rest_framework as filters

from apps.catalog.models.product import Product


class ProductFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name="category_id")
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    status = filters.CharFilter(field_name="status", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "name", "status"]