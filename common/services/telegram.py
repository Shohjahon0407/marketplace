import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(text: str) -> bool:
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "")

    if not bot_token or not chat_id:
        logger.warning("Telegram settings not configured.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.exception("Telegram message sending failed: %s", exc)
        return False


def format_order_notification(order) -> str:
    user_name = getattr(order.user, "name", "") or getattr(order.user, "email", "Unknown user")
    items_count = order.items.count()

    return (
        f"🛒 <b>Yangi order yaratildi</b>\n\n"
        f"<b>Order code:</b> {order.order_code}\n"
        f"<b>Mijoz:</b> {user_name}\n"
        f"<b>Yetkazib berish:</b> {order.delivery_method}\n"
        f"<b>Status:</b> {order.status}\n"
        f"<b>Mahsulotlar soni:</b> {items_count}\n"
        f"<b>Jami summa:</b> {order.total_price}\n"
    )


def send_new_order_notification(order) -> bool:
    message = format_order_notification(order)
    return send_telegram_message(message)
