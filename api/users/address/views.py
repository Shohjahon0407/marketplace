from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.models.address import Address
from .serializers import (
    AddressReadSerializer,
    AddressCreateSerializer,
    AddressUpdateSerializer,
)


class BaseAddressAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressReadSerializer
    queryset = Address.objects.all()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()

        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return Address.objects.none()

        return self.queryset.filter(user_id=user.id).order_by("-is_default", "-created_at")

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), id=pk)

    def get_address_response(self, address, request, status_code=status.HTTP_200_OK):
        serializer = AddressReadSerializer(address, context={"request": request})
        return Response(serializer.data, status=status_code)


class AddressListCreateAPIView(BaseAddressAPIView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = AddressReadSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = AddressCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return self.get_address_response(address, request, status.HTTP_201_CREATED)


class AddressDetailAPIView(BaseAddressAPIView):
    def get(self, request, pk, *args, **kwargs):
        address = self.get_object(pk)
        return self.get_address_response(address, request)

    def patch(self, request, pk, *args, **kwargs):
        address = self.get_object(pk)
        serializer = AddressUpdateSerializer(
            address,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return self.get_address_response(address, request)

    def delete(self, request, pk, *args, **kwargs):
        address = self.get_object(pk)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DefaultAddressAPIView(BaseAddressAPIView):
    def get(self, request, *args, **kwargs):
        address = self.get_queryset().filter(is_default=True).first()
        if not address:
            return Response(
                {"detail": "Default address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return self.get_address_response(address, request)