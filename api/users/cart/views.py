from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cart.models import Cart, CartItem
from .serializers import (
    CartReadSerializer,
    AddProductToCartSerializer,
    CartItemUpdateSerializer,
)


def get_or_restore_cart(user):
    if not getattr(user, "is_authenticated", False):
        raise NotAuthenticated("Authentication credentials were not provided.")

    cart = Cart.all_objects.filter(user_id=user.id).first()

    if cart:
        if cart.is_deleted:
            cart.restore()
        return cart

    return Cart.objects.create(user=user)


class BaseCartAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartReadSerializer  # ENG MUHIM JOY

    def get_cart(self):
        return get_or_restore_cart(self.request.user)

    def get_prefetched_cart(self, cart_id):
        return Cart.objects.prefetch_related(
            "items__product__detail",
            "items__product__images",
        ).get(id=cart_id)

    def get_cart_response(self, cart, request, status_code=status.HTTP_200_OK):
        serializer = CartReadSerializer(cart, context={"request": request})
        return Response(serializer.data, status=status_code)


class CartCreateAPIView(BaseCartAPIView):
    def post(self, request, *args, **kwargs):
        cart = self.get_cart()
        cart = self.get_prefetched_cart(cart.id)
        return self.get_cart_response(cart, request, status.HTTP_201_CREATED)


class AddProductToCartAPIView(BaseCartAPIView):
    serializer_class = AddProductToCartSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product_obj"]
        quantity = serializer.validated_data["quantity"]

        cart = self.get_cart()

        cart_item = CartItem.objects.filter(
            cart_id=cart.id,
            product_id=product.id,
        ).first()

        if cart_item:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.detail.stock:
                return Response(
                    {"quantity": "Requested quantity exceeds available stock."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_quantity
            cart_item.save(update_fields=["quantity"])
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
            )

        cart = self.get_prefetched_cart(cart.id)
        return self.get_cart_response(cart, request)


class CartItemUpdateDeleteAPIView(BaseCartAPIView):
    serializer_class = CartItemUpdateSerializer
    queryset = CartItem.objects.select_related("cart", "product__detail")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CartItem.objects.none()

        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return CartItem.objects.none()

        return self.queryset.filter(cart__user_id=user.id)

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), id=pk)

    def patch(self, request, pk, *args, **kwargs):
        cart_item = self.get_object(pk)

        serializer = self.get_serializer(cart_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        cart = self.get_prefetched_cart(cart_item.cart_id)
        return self.get_cart_response(cart, request)

    def delete(self, request, pk, *args, **kwargs):
        cart_item = self.get_object(pk)
        cart_id = cart_item.cart_id
        cart_item.delete()

        cart = self.get_prefetched_cart(cart_id)
        return self.get_cart_response(cart, request)


class CartDetailAPIView(BaseCartAPIView):
    def get(self, request, *args, **kwargs):
        cart = self.get_cart()
        cart = self.get_prefetched_cart(cart.id)
        return self.get_cart_response(cart, request)
