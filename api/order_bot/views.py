from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.order_bot.services import process_update
from rest_framework import serializers


class TelegramWebhookSerializer(serializers.Serializer):
    pass

class TelegramWebhookAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = TelegramWebhookSerializer
    authentication_classes = []
    queryset = []

    def post(self, request, *args, **kwargs):
        secret = kwargs.get("secret")
        expected_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")

        if expected_secret and secret != expected_secret:
            return Response({"detail": "Invalid webhook secret."}, status=status.HTTP_403_FORBIDDEN)

        process_update(request.data)
        return Response({"ok": True}, status=status.HTTP_200_OK)