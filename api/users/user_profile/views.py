from rest_framework import request, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.users.orders.serializers import OrderListSerializer
from api.users.user_profile.serializers import ProfileListSerializer, ProfileUpdateSerializer, ProfileCreateSerializer
from apps.accounts.models import Profile
from apps.orders.models import Order
from common.enums.enums import OrderStatus


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.select_related("user").all()
    http_method_names = ["get", "post", "patch"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileListSerializer
        elif self.action == "create":
            return ProfileCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ProfileUpdateSerializer
        return ProfileListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        response_serializer = ProfileListSerializer(
            profile,
            context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        response_serializer = ProfileListSerializer(
            profile,
            context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class NewOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Order.objects.filter(user=request.user, status=OrderStatus.PENDING).order_by("-created_at")
        serializer = OrderListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AllOrdersListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
