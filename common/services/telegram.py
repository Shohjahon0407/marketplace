import logging
from typing import Optional

import requests
from django.conf import settings

from apps.orders.models import Order

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"

STATUS_LABELS = {
    "pending": "Pending",
    "confirmed": "Confirmed",
    "cancelled": "Cancelled",
    "delivered": "Delivered",
    "all": "Barcha",
}


def _get_bot_token() -> str:
    return getattr(settings, "TELEGRAM_BOT_TOKEN", "")


def _get_default_chat_id() -> str:
    return str(getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", ""))


def _build_url(method: str) -> str:
    return TELEGRAM_API_URL.format(token=_get_bot_token(), method=method)


def _post_to_telegram(method: str, payload: dict) -> bool:
    bot_token = _get_bot_token()
    if not bot_token:
        logger.warning("Telegram bot token not configured.")
        return False

    try:
        response = requests.post(_build_url(method), json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.exception("Telegram API request failed: %s", exc)
        return False


def send_telegram_message(
    text: str,
    reply_markup: Optional[dict] = None,
    chat_id: Optional[str] = None,
) -> bool:
    target_chat_id = str(chat_id or _get_default_chat_id())

    if not target_chat_id:
        logger.warning("Telegram chat id not configured.")
        return False

    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    return _post_to_telegram("sendMessage", payload)


def edit_telegram_message(
    chat_id: str,
    message_id: int,
    text: str,
    reply_markup: Optional[dict] = None,
) -> bool:
    payload = {
        "chat_id": str(chat_id),
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    return _post_to_telegram("editMessageText", payload)


def answer_callback_query(callback_query_id: str, text: str = "") -> bool:
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    return _post_to_telegram("answerCallbackQuery", payload)


def build_main_menu_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "📦 Filterlar"}, {"text": "📋 Barcha orderlar"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def build_orders_filter_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🟡 Pending", "callback_data": "orders:pending"},
                {"text": "🟢 Confirmed", "callback_data": "orders:confirmed"},
            ],
            [
                {"text": "🚚 Delivered", "callback_data": "orders:delivered"},
                {"text": "❌ Cancelled", "callback_data": "orders:cancelled"},
            ],
            [
                {"text": "📋 All", "callback_data": "orders:all"},
            ],
        ]
    }


def format_order_notification(order) -> str:
    user_name = getattr(order.user, "name", "") or getattr(order.user, "phone", "Unknown user")
    items_count = order.items.count()
    product = getattr(order.product, "name", "")

    order_taking = "Do'konga kelib olib ketadi"
    if getattr(order, "delivery_method", "") == "courier":
        address = getattr(order, "delivery_address", "") or "Manzil kiritilmagan"
        order_taking = f"Yetkazib berish manzili: {address}"

    return (
        f"🛒 <b>Yangi order yaratildi</b>\n\n"
        f"<b>Order code:</b> {order.order_code}\n"
        f"<b>Order code:</b> {product}\n"
        f"<b>Mijoz:</b> {user_name}\n"
        f"<b>Mahsulotni topshirish:</b> {order_taking}\n"
        f"<b>Status:</b> {order.status}\n"
        f"<b>Mahsulotlar soni:</b> {items_count}\n"
        f"<b>Jami summa:</b> {order.total_price}\n"
    )


def send_new_order_notification(order) -> bool:
    return send_telegram_message(
        text=format_order_notification(order),
        reply_markup=build_orders_filter_keyboard(),
    )


def get_orders_by_status(status_value: str):
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    if status_value != "all":
        queryset = queryset.filter(status=status_value)

    return list(queryset[:20])


def format_orders_list_message(orders, status_label: str) -> str:
    if not orders:
        return f"📭 <b>{status_label}</b> statusida orderlar topilmadi."

    lines = [f"📦 <b>{status_label}</b> statusidagi orderlar:"]

    for order in orders:
        user_name = getattr(order.user, "name", "") or getattr(order.user, "phone", "Unknown user")
        lines.append(
            f"\n• <b>{order.order_code}</b>\n"
            f"  Mijoz: {user_name}\n"
            f"  Status: {order.status}\n"
            f"  Summa: {order.total_price}\n"
        )

    return "\n".join(lines)