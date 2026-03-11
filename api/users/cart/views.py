from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart, CartItem
from .serializers import (
    CartReadSerializer,
    AddProductToCartSerializer, CartItemUpdateSerializer,
)


def get_or_restore_cart(user):
    cart = Cart.all_objects.filter(user=user).first()

    if cart:
        if cart.is_deleted:
            cart.restore()
        return cart

    return Cart.objects.create(user=user)


class CartCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_or_restore_cart(request.user)

        cart = Cart.objects.prefetch_related(
            "items__product__detail",
            "items__product__images",
        ).get(id=cart.id)

        serializer = CartReadSerializer(cart, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def get_or_restore_cart(user):
    cart = Cart.all_objects.filter(user=user).first()
    if cart:
        if cart.is_deleted:
            cart.restore()
        return cart
    return Cart.objects.create(user=user)


class AddProductToCartAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddProductToCartSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product_obj"]
        quantity = serializer.validated_data["quantity"]

        cart = get_or_restore_cart(request.user)

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if cart_item:
            if cart_item.is_deleted:
                cart_item.restore()
                cart_item.quantity = 0

            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.detail.stock:
                return Response(
                    {"quantity": "Requested quantity exceeds available stock."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_quantity
            cart_item.save(update_fields=["quantity", "updated_at"])
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
            )

        cart = Cart.objects.prefetch_related(
            "items__product__detail",
            "items__product__images",
        ).get(id=cart.id)

        response_serializer = CartReadSerializer(cart, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CartItemUpdateDeleteAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemUpdateSerializer

    def get_object(self, pk, user):
        return get_object_or_404(
            CartItem.objects.select_related("cart", "product__detail"),
            id=pk,
            cart__user=user,
        )

    def patch(self, request, pk):
        cart_item = self.get_object(pk, request.user)

        serializer = self.get_serializer(cart_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        cart = Cart.objects.prefetch_related(
            "items__product__detail",
            "items__product__images",
        ).get(id=cart_item.cart_id)

        return Response(
            CartReadSerializer(cart, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        cart_item = self.get_object(pk, request.user)
        cart_id = cart_item.cart_id
        cart_item.delete()

        cart = Cart.objects.prefetch_related(
            "items__product__detail",
            "items__product__images",
        ).get(id=cart_id)

        return Response(
            CartReadSerializer(cart, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_restore_cart(request.user)

        cart = Cart.objects.prefetch_related(
            "items__product__detail",
            "items__product__images",
        ).get(id=cart.id)

        serializer = CartReadSerializer(cart, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)