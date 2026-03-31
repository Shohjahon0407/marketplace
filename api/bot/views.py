from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import serializers

from common.services.telegram import (
    STATUS_LABELS,
    answer_callback_query,
    build_main_menu_keyboard,
    build_orders_filter_keyboard,
    edit_telegram_message,
    format_orders_list_message,
    get_orders_by_status,
    send_telegram_message,
)


class TelegramWebhookSerializer(serializers.Serializer):
    pass

class TelegramWebhookAPIView(generics.GenericAPIView):
    serializer_class = TelegramWebhookSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data

        if "message" in data:
            self._handle_message(data["message"])

        if "callback_query" in data:
            self._handle_callback_query(data["callback_query"])

        return Response({"ok": True}, status=status.HTTP_200_OK)

    def _handle_message(self, message: dict) -> None:
        text = (message.get("text") or "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))

        if not chat_id:
            return

        if text == "/start":
            send_telegram_message(
                text="Assalomu alaykum. Pastdagi menyudan kerakli bo‘limni tanlang.",
                reply_markup=build_main_menu_keyboard(),
                chat_id=chat_id,
            )
            return

        if text in ["/orders", "📦 Filterlar"]:
            send_telegram_message(
                text="Qaysi statusdagi orderlarni ko‘rmoqchisiz?",
                reply_markup=build_orders_filter_keyboard(),
                chat_id=chat_id,
            )
            return

        if text == "📋 Barcha orderlar":
            orders = get_orders_by_status("all")
            send_telegram_message(
                text=format_orders_list_message(orders, STATUS_LABELS["all"]),
                reply_markup=build_main_menu_keyboard(),
                chat_id=chat_id,
            )
            return

    def _handle_callback_query(self, callback_query: dict) -> None:
        callback_query_id = callback_query.get("id", "")
        callback_data = callback_query.get("data", "")
        message = callback_query.get("message", {})

        chat_id = str(message.get("chat", {}).get("id", ""))
        message_id = message.get("message_id")

        if not callback_data.startswith("orders:"):
            if callback_query_id:
                answer_callback_query(callback_query_id, "Noto‘g‘ri action")
            return

        status_value = callback_data.split(":", 1)[1]

        if status_value not in STATUS_LABELS:
            if callback_query_id:
                answer_callback_query(callback_query_id, "Noto‘g‘ri status")
            return

        orders = get_orders_by_status(status_value)
        text = format_orders_list_message(orders, STATUS_LABELS[status_value])

        if callback_query_id:
            answer_callback_query(callback_query_id, STATUS_LABELS[status_value])

        if chat_id and message_id:
            edit_telegram_message(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=build_orders_filter_keyboard(),
            )