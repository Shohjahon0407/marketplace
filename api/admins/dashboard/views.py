from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.accounts.models import User
from apps.orders.models import Order
from apps.catalog.models.product import Product
from django.db.models import Sum


class AdminDashboardOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Buyurtmalar soni
        total_orders = Order.objects.count()

        # Tasdiqlangan buyurtmalar soni
        total_confirmed_orders = Order.objects.filter(status="confirmed").count()

        # Foydalanuvchilar soni
        total_users = User.objects.count()

        # Mahsulotlar soni
        total_products = Product.objects.count()

        # Mahsulotlar sotilishi bo‘yicha umumiy qiymat (savdo)
        total_sales_value = Order.objects.filter(status="confirmed").aggregate(Sum('total_price'))["total_price__sum"]

        data = {
            "total_orders": total_orders,
            "total_confirmed_orders": total_confirmed_orders,
            "total_users": total_users,
            "total_products": total_products,
            "total_sales_value": total_sales_value if total_sales_value else 0,
        }

        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_summary="Admin Dashboard Overview")
    def get(self, request):
        total_orders = Order.objects.count()
        total_confirmed_orders = Order.objects.filter(status="confirmed").count()
        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_sales_value = Order.objects.filter(status="confirmed").aggregate(Sum('total_price'))["total_price__sum"]

        data = {
            "total_orders": total_orders,
            "total_confirmed_orders": total_confirmed_orders,
            "total_users": total_users,
            "total_products": total_products,
            "total_sales_value": total_sales_value if total_sales_value else 0,
        }

        return Response(data, status=status.HTTP_200_OK)