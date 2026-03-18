from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.catalog.models.product import Product
from apps.wishlist.models import Wishlist
from .serializers import WishlistSerializer


class WishlistCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Sevimli mahsulotni qo'shish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.FORMAT_UUID, description="Product ID")
            },
        ),
        responses={201: WishlistSerializer},
    )
    def post(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        user = request.user

        # Mahsulotni tekshirish
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        # Foydalanuvchi allaqachon mahsulotni sevimlilarga qo‘shgan bo‘lmasligi uchun tekshiruv
        if Wishlist.objects.filter(user=user, product=product).exists():
            return Response({"detail": "Product is already in your wishlist."}, status=status.HTTP_400_BAD_REQUEST)

        # Sevimlilarga qo‘shish
        wishlist_item = Wishlist.objects.create(user=user, product=product)
        serializer = WishlistSerializer(wishlist_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WishlistListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        wishlist = Wishlist.objects.filter(user=user).select_related("product")

        serializer = WishlistSerializer(wishlist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WishlistDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get("product_id")
        user = request.user

        try:
            wishlist_item = Wishlist.objects.get(user=user, product=product_id)
            wishlist_item.delete()
            return Response({"detail": "Product removed from wishlist."}, status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response({"detail": "Product not found in your wishlist."}, status=status.HTTP_404_NOT_FOUND)
