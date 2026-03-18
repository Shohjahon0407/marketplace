from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.orders.models import Order
from api.admins.orders.serializers import (
    AdminOrderListSerializer,
    AdminOrderDetailSerializer,
    AdminOrderStatusUpdateSerializer,
    AdminPickupByCodeSerializer,
)


class AdminOrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "order_code",
        "delivery_address",
        "comment",
        "user__email",
        # "user__phone_number",
        "items__product_name",
    ]
    ordering_fields = ["created_at", "total_price", "subtotal"]
    ordering = ["-created_at"]

    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("items", "items__product")
        .filter(is_deleted=False)
        .order_by("-created_at")
    )

    def get_serializer_class(self):
        if self.action == "list":
            return AdminOrderListSerializer
        if self.action == "retrieve":
            return AdminOrderDetailSerializer
        if self.action in ["partial_update", "update"]:
            return AdminOrderStatusUpdateSerializer
        if self.action == "pickup_by_code":
            return AdminPickupByCodeSerializer
        return AdminOrderDetailSerializer

    def get_queryset(self):
        queryset = self.queryset

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        delivery_method = self.request.query_params.get("delivery_method")
        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)

        user_id = self.request.query_params.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        order_code = self.request.query_params.get("order_code")
        if order_code:
            queryset = queryset.filter(order_code__icontains=order_code)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        output = AdminOrderDetailSerializer(instance, context={"request": request})
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="pickup-by-code")
    def pickup_by_code(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        output = AdminOrderDetailSerializer(order, context={"request": request})
        return Response(output.data, status=status.HTTP_200_OK)