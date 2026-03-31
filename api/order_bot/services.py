import logging
import requests

from django.conf import settings
from django.utils import timezone

from apps.orders.models import Order
from common.enums.enums import OrderStatus, DeliveryMethod
from common.enums.telegram_bot import TelegramUserState, TelegramAdminState, PaymentFlowStatus
from apps.telegram_bot.models import (
    TelegramProfile,
    TelegramBotAdmin,
    BotSetting,
    BotAdminContact,
    OrderPaymentFlow,
)

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


def telegram_request(method: str, payload: dict | None = None) -> dict:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return {"ok": False, "description": "Bot token not configured"}

    url = TELEGRAM_API_URL.format(token=token, method=method)

    try:
        response = requests.post(url, json=payload or {}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.exception("Telegram request failed: %s", exc)
        return {"ok": False, "description": str(exc)}


def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    result = telegram_request("sendMessage", payload)
    logger.info("sendMessage result: %s", result)


def answer_callback_query(callback_query_id: str, text: str = "") -> None:
    telegram_request("answerCallbackQuery", {
        "callback_query_id": callback_query_id,
        "text": text,
    })


def remove_keyboard(chat_id: int, text: str) -> None:
    send_message(chat_id, text, {"remove_keyboard": True})


def request_phone(chat_id: int) -> None:
    send_message(
        chat_id,
        "Telefon raqamingizni yuboring.",
        reply_markup={
            "keyboard": [[{"text": "📱 Telefonni yuborish", "request_contact": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        },
    )


def request_location(chat_id: int) -> None:
    send_message(
        chat_id,
        "Endi yetkazib berish lokatsiyasini yuboring.",
        reply_markup={
            "keyboard": [[{"text": "📍 Lokatsiyani yuborish", "request_location": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        },
    )


def get_admin_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "💳 Karta sozlamalari", "callback_data": "admin:set_card"}],
            [{"text": "👤 Admin kontakt qo'shish", "callback_data": "admin:add_contact"}],
            [{"text": "📋 Kontaktlar ro'yxati", "callback_data": "admin:list_contacts"}],
            [{"text": "🧾 Kutilayotgan cheklar", "callback_data": "admin:pending_receipts"}],
        ]
    }


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def get_or_create_profile(tg_user: dict, chat: dict) -> TelegramProfile:
    profile, _ = TelegramProfile.objects.get_or_create(
        telegram_user_id=tg_user["id"],
        defaults={
            "telegram_chat_id": chat["id"],
            "username": tg_user.get("username", "") or "",
            "first_name": tg_user.get("first_name", "") or "",
            "last_name": tg_user.get("last_name", "") or "",
        },
    )
    profile.telegram_chat_id = chat["id"]
    profile.username = tg_user.get("username", "") or ""
    profile.first_name = tg_user.get("first_name", "") or ""
    profile.last_name = tg_user.get("last_name", "") or ""
    profile.save(update_fields=[
        "telegram_chat_id",
        "username",
        "first_name",
        "last_name",
        "updated_at",
    ])
    return profile


def get_admin_by_tg_user_id(telegram_user_id: int):
    return TelegramBotAdmin.objects.filter(
        telegram_user_id=telegram_user_id,
        is_active=True,
    ).first()


def get_bot_setting() -> BotSetting:
    setting = BotSetting.objects.filter(is_active=True).order_by("-id").first()
    if setting:
        return setting
    return BotSetting.objects.create(is_active=True)


def get_admin_contacts_text() -> str:
    contacts = BotAdminContact.objects.filter(is_active=True).order_by("id")
    if not contacts.exists():
        return "Admin kontaktlari kiritilmagan."

    lines = ["<b>Admin kontaktlari</b>"]
    for item in contacts:
        username = f"@{item.telegram_username}" if item.telegram_username else "-"
        phone = item.phone or "-"
        lines.append(f"• {item.full_name} | {username} | {phone}")
    return "\n".join(lines)


def send_admin_menu(admin: TelegramBotAdmin) -> None:
    send_message(
        admin.telegram_chat_id,
        "Admin paneliga xush kelibsiz.",
        reply_markup=get_admin_menu_keyboard(),
    )


def find_pending_orders_by_phone_safe(phone: str):
    normalized = normalize_phone(phone)
    if len(normalized) < 7:
        return []

    qs = (
        Order.objects
        .select_related("user")
        .filter(
            status=OrderStatus.PENDING,
            delivery_method=DeliveryMethod.COURIER,
            is_deleted=False,
        )
        .order_by("-created_at")
    )

    matched = []
    for order in qs:
        user_phone = normalize_phone(getattr(order.user, "phone", "") or "")
        if user_phone and user_phone.endswith(normalized[-9:]):
            matched.append(order)
    return matched


def send_order_choices(profile: TelegramProfile, phone: str) -> None:
    profile.phone = phone
    profile.state = TelegramUserState.WAIT_PHONE
    profile.selected_order = None
    profile.save(update_fields=["phone", "state", "selected_order", "updated_at"])

    orders = find_pending_orders_by_phone_safe(phone)
    if not orders:
        send_message(
            profile.telegram_chat_id,
            "❌ Bu telefon raqamga tegishli pending order topilmadi.\nQaytadan kiriting yoki admin bilan bog'laning."
        )
        send_message(profile.telegram_chat_id, get_admin_contacts_text())
        return

    keyboard = []
    for order in orders[:10]:
        keyboard.append([{
            "text": f"{order.order_code} | {order.total_price}",
            "callback_data": f"select_order:{order.id}",
        }])

    send_message(
        profile.telegram_chat_id,
        "Quyidagi pending orderlardan birini tanlang:",
        reply_markup={"inline_keyboard": keyboard},
    )


def start_payment_flow(profile: TelegramProfile, order: Order) -> OrderPaymentFlow:
    setting = get_bot_setting()

    flow, _ = OrderPaymentFlow.objects.get_or_create(
        order=order,
        defaults={
            "telegram_profile": profile,
            "status": PaymentFlowStatus.WAITING_RECEIPT,
            "amount_snapshot": order.total_price,
            "card_number_snapshot": setting.payment_card_number,
            "card_owner_snapshot": setting.payment_card_owner,
        },
    )

    flow.telegram_profile = profile
    flow.status = PaymentFlowStatus.WAITING_RECEIPT
    flow.amount_snapshot = order.total_price
    flow.card_number_snapshot = setting.payment_card_number
    flow.card_owner_snapshot = setting.payment_card_owner
    flow.save(update_fields=[
        "telegram_profile",
        "status",
        "amount_snapshot",
        "card_number_snapshot",
        "card_owner_snapshot",
        "updated_at",
    ])

    profile.selected_order = order
    profile.state = TelegramUserState.WAIT_RECEIPT
    profile.save(update_fields=["selected_order", "state", "updated_at"])

    return flow


def send_payment_info(profile: TelegramProfile, order: Order) -> None:
    flow = start_payment_flow(profile, order)
    user_name = getattr(order.user, "name", "") or getattr(order.user, "email", "Unknown")
    user_phone = getattr(order.user, "phone", "") or "-"

    text = (
        f"✅ <b>Order tanlandi</b>\n\n"
        f"<b>Order code:</b> {order.order_code}\n"
        f"<b>Ism:</b> {user_name}\n"
        f"<b>Telefon:</b> {user_phone}\n"
        f"<b>To'lov summasi:</b> {flow.amount_snapshot}\n\n"
        f"<b>Karta raqami:</b> {flow.card_number_snapshot or '-'}\n"
        f"<b>Karta egasi:</b> {flow.card_owner_snapshot or '-'}\n\n"
        f"Shu kartaga to'lov qilib, chek rasmini yuboring."
    )
    send_message(profile.telegram_chat_id, text)


def notify_admins_about_receipt(flow: OrderPaymentFlow) -> None:
    admins = TelegramBotAdmin.objects.filter(is_active=True)
    if not admins.exists():
        return

    order = flow.order
    user_name = getattr(order.user, "name", "") or getattr(order.user, "email", "Unknown")
    user_phone = getattr(order.user, "phone", "") or "-"

    text = (
        f"🧾 <b>Yangi chek yuborildi</b>\n\n"
        f"<b>Order code:</b> {order.order_code}\n"
        f"<b>Mijoz:</b> {user_name}\n"
        f"<b>Telefon:</b> {user_phone}\n"
        f"<b>Summa:</b> {flow.amount_snapshot}\n"
        f"<b>Status:</b> {flow.status}\n\n"
        f"Chekni tekshirib tasdiqlang yoki rad eting."
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Tasdiqlash", "callback_data": f"approve_payment:{flow.id}"},
                {"text": "❌ Rad etish", "callback_data": f"reject_payment:{flow.id}"},
            ]
        ]
    }

    for admin in admins:
        send_message(admin.telegram_chat_id, text, reply_markup=keyboard)
        if flow.receipt_file_id:
            telegram_request("sendPhoto", {
                "chat_id": admin.telegram_chat_id,
                "photo": flow.receipt_file_id,
            })


def send_pending_receipts(chat_id: int) -> None:
    flows = (
        OrderPaymentFlow.objects
        .select_related("order", "telegram_profile")
        .filter(status=PaymentFlowStatus.LOCATION_UPLOADED)
        .order_by("-updated_at")[:10]
    )

    if not flows:
        send_message(chat_id, "Kutilayotgan cheklar yo'q.")
        return

    for flow in flows:
        user_name = getattr(flow.order.user, "name", "") or getattr(flow.order.user, "email", "Unknown")
        text = (
            f"🧾 <b>Tekshiruv kutilmoqda</b>\n\n"
            f"<b>Order:</b> {flow.order.order_code}\n"
            f"<b>Mijoz:</b> {user_name}\n"
            f"<b>Summa:</b> {flow.amount_snapshot}\n"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Tasdiqlash", "callback_data": f"approve_payment:{flow.id}"},
                    {"text": "❌ Rad etish", "callback_data": f"reject_payment:{flow.id}"},
                ]
            ]
        }
        send_message(chat_id, text, reply_markup=keyboard)
        if flow.receipt_file_id:
            telegram_request("sendPhoto", {
                "chat_id": chat_id,
                "photo": flow.receipt_file_id,
            })


def approve_payment(flow: OrderPaymentFlow) -> None:
    flow.status = PaymentFlowStatus.APPROVED
    flow.save(update_fields=["status", "updated_at"])

    profile = flow.telegram_profile
    if profile:
        profile.state = TelegramUserState.DONE
        profile.save(update_fields=["state", "updated_at"])
        remove_keyboard(
            profile.telegram_chat_id,
            f"✅ To'lov tasdiqlandi.\nOrder: <b>{flow.order.order_code}</b>\nBuyurtmangiz qabul qilindi."
        )


def reject_payment(flow: OrderPaymentFlow) -> None:
    flow.status = PaymentFlowStatus.REJECTED
    flow.save(update_fields=["status", "updated_at"])

    profile = flow.telegram_profile
    if profile:
        profile.state = TelegramUserState.WAIT_RECEIPT
        profile.save(update_fields=["state", "updated_at"])
        send_message(
            profile.telegram_chat_id,
            f"❌ To'lov tasdiqlanmadi.\nOrder: <b>{flow.order.order_code}</b>\nChekni qaytadan yuboring."
        )


def handle_start(message: dict) -> None:
    profile = get_or_create_profile(message["from"], message["chat"])
    profile.state = TelegramUserState.WAIT_PHONE
    profile.selected_order = None
    profile.save(update_fields=["state", "selected_order", "updated_at"])
    request_phone(profile.telegram_chat_id)


def handle_contact_message(message: dict) -> None:
    profile = get_or_create_profile(message["from"], message["chat"])
    contact = message.get("contact") or {}
    phone = contact.get("phone_number", "")

    if not phone:
        send_message(profile.telegram_chat_id, "Telefon topilmadi. Qayta yuboring.")
        return

    send_order_choices(profile, phone)


def handle_order_selection(callback_query: dict) -> None:
    callback_data = callback_query.get("data", "")
    _, order_id = callback_data.split(":")
    tg_user = callback_query["from"]
    message = callback_query["message"]
    profile = get_or_create_profile(tg_user, message["chat"])

    try:
        order = Order.objects.select_related("user").get(id=order_id, is_deleted=False)
    except Order.DoesNotExist:
        answer_callback_query(callback_query["id"], "Order topilmadi")
        send_message(profile.telegram_chat_id, "Order topilmadi.")
        return

    answer_callback_query(callback_query["id"], "Order tanlandi")
    send_payment_info(profile, order)


def handle_photo_message(message: dict) -> None:
    profile = get_or_create_profile(message["from"], message["chat"])

    if profile.state != TelegramUserState.WAIT_RECEIPT or not profile.selected_order_id:
        send_message(profile.telegram_chat_id, "Avval /start bosing va order tanlang.")
        return

    photo_list = message.get("photo") or []
    if not photo_list:
        send_message(profile.telegram_chat_id, "Foto topilmadi.")
        return

    largest_photo = photo_list[-1]
    file_id = largest_photo.get("file_id", "")

    flow = OrderPaymentFlow.objects.filter(order=profile.selected_order).first()
    if not flow:
        send_message(profile.telegram_chat_id, "Payment flow topilmadi.")
        return

    flow.receipt_file_id = file_id
    flow.receipt_uploaded_at = timezone.now()
    flow.status = PaymentFlowStatus.RECEIPT_UPLOADED
    flow.save(update_fields=[
        "receipt_file_id",
        "receipt_uploaded_at",
        "status",
        "updated_at",
    ])

    profile.state = TelegramUserState.WAIT_LOCATION
    profile.save(update_fields=["state", "updated_at"])

    send_message(profile.telegram_chat_id, "✅ Chek qabul qilindi.")
    request_location(profile.telegram_chat_id)


def handle_location_message(message: dict) -> None:
    profile = get_or_create_profile(message["from"], message["chat"])

    if profile.state != TelegramUserState.WAIT_LOCATION or not profile.selected_order_id:
        send_message(profile.telegram_chat_id, "Avval /start bosing.")
        return

    location = message.get("location") or {}
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        send_message(profile.telegram_chat_id, "Lokatsiya topilmadi.")
        return

    flow = OrderPaymentFlow.objects.filter(order=profile.selected_order).first()
    if not flow:
        send_message(profile.telegram_chat_id, "Payment flow topilmadi.")
        return

    flow.location_latitude = latitude
    flow.location_longitude = longitude
    flow.location_uploaded_at = timezone.now()
    flow.status = PaymentFlowStatus.LOCATION_UPLOADED
    flow.save(update_fields=[
        "location_latitude",
        "location_longitude",
        "location_uploaded_at",
        "status",
        "updated_at",
    ])

    notify_admins_about_receipt(flow)
    remove_keyboard(
        profile.telegram_chat_id,
        "📍 Lokatsiya qabul qilindi. Adminlar to'lovni tekshiradi."
    )


def handle_admin_menu_callback(callback_query: dict) -> None:
    tg_user = callback_query["from"]
    message = callback_query["message"]
    callback_data = callback_query.get("data", "")
    callback_id = callback_query["id"]

    admin = get_admin_by_tg_user_id(tg_user["id"])
    if not admin:
        answer_callback_query(callback_id, "Siz admin emassiz")
        return

    admin.telegram_chat_id = message["chat"]["id"]
    admin.save(update_fields=["telegram_chat_id", "updated_at"])

    if callback_data == "admin:set_card":
        admin.state = TelegramAdminState.WAIT_CARD_NUMBER
        admin.save(update_fields=["state", "updated_at"])
        answer_callback_query(callback_id, "Karta raqamini kiriting")
        send_message(admin.telegram_chat_id, "Yangi karta raqamini kiriting:")
        return

    if callback_data == "admin:add_contact":
        admin.state = TelegramAdminState.WAIT_CONTACT_NAME
        admin.temp_full_name = ""
        admin.temp_username = ""
        admin.save(update_fields=["state", "temp_full_name", "temp_username", "updated_at"])
        answer_callback_query(callback_id, "Kontakt ismini kiriting")
        send_message(admin.telegram_chat_id, "Admin kontakt ism-familyasini kiriting:")
        return

    if callback_data == "admin:list_contacts":
        answer_callback_query(callback_id, "Kontaktlar")
        send_message(admin.telegram_chat_id, get_admin_contacts_text())
        return

    if callback_data == "admin:pending_receipts":
        answer_callback_query(callback_id, "Kutilayotgan cheklar")
        send_pending_receipts(admin.telegram_chat_id)
        return


def handle_admin_text_message(message: dict) -> bool:
    tg_user = message["from"]
    text = (message.get("text") or "").strip()

    admin = get_admin_by_tg_user_id(tg_user["id"])
    if not admin:
        return False

    admin.telegram_chat_id = message["chat"]["id"]
    admin.username = tg_user.get("username", "") or ""
    admin.full_name = f'{tg_user.get("first_name", "")} {tg_user.get("last_name", "")}'.strip()
    admin.save(update_fields=["telegram_chat_id", "username", "full_name", "updated_at"])

    if text == "/admin":
        admin.state = TelegramAdminState.IDLE
        admin.save(update_fields=["state", "updated_at"])
        send_admin_menu(admin)
        return True

    if admin.state == TelegramAdminState.WAIT_CARD_NUMBER:
        setting = get_bot_setting()
        setting.payment_card_number = text
        setting.save(update_fields=["payment_card_number", "updated_at"])

        admin.state = TelegramAdminState.WAIT_CARD_OWNER
        admin.save(update_fields=["state", "updated_at"])

        send_message(admin.telegram_chat_id, "Karta egasi ism-familyasini kiriting:")
        return True

    if admin.state == TelegramAdminState.WAIT_CARD_OWNER:
        setting = get_bot_setting()
        setting.payment_card_owner = text
        setting.save(update_fields=["payment_card_owner", "updated_at"])

        admin.state = TelegramAdminState.IDLE
        admin.save(update_fields=["state", "updated_at"])

        send_message(admin.telegram_chat_id, "✅ Karta ma'lumotlari saqlandi.")
        send_admin_menu(admin)
        return True

    if admin.state == TelegramAdminState.WAIT_CONTACT_NAME:
        admin.temp_full_name = text
        admin.state = TelegramAdminState.WAIT_CONTACT_USERNAME
        admin.save(update_fields=["temp_full_name", "state", "updated_at"])

        send_message(admin.telegram_chat_id, "Telegram username kiriting. @ bilan yoki usiz:")
        return True

    if admin.state == TelegramAdminState.WAIT_CONTACT_USERNAME:
        admin.temp_username = text.replace("@", "")
        admin.state = TelegramAdminState.WAIT_CONTACT_PHONE
        admin.save(update_fields=["temp_username", "state", "updated_at"])

        send_message(admin.telegram_chat_id, "Telefon raqamini kiriting:")
        return True

    if admin.state == TelegramAdminState.WAIT_CONTACT_PHONE:
        BotAdminContact.objects.create(
            full_name=admin.temp_full_name,
            telegram_username=admin.temp_username,
            phone=text,
            is_active=True,
        )

        admin.temp_full_name = ""
        admin.temp_username = ""
        admin.state = TelegramAdminState.IDLE
        admin.save(update_fields=["temp_full_name", "temp_username", "state", "updated_at"])

        send_message(admin.telegram_chat_id, "✅ Admin kontakt saqlandi.")
        send_admin_menu(admin)
        return True

    return False


def handle_text_message(message: dict) -> None:
    profile = get_or_create_profile(message["from"], message["chat"])
    text = (message.get("text") or "").strip()

    if text == "/start":
        handle_start(message)
        return

    if text.lower() in {"/admin_contacts", "admin", "kontakt"}:
        send_message(profile.telegram_chat_id, get_admin_contacts_text())
        return

    if profile.state == TelegramUserState.WAIT_PHONE:
        send_order_choices(profile, text)
        return

    if profile.state == TelegramUserState.WAIT_RECEIPT:
        send_message(profile.telegram_chat_id, "Chek rasmini yuboring.")
        return

    if profile.state == TelegramUserState.WAIT_LOCATION:
        request_location(profile.telegram_chat_id)
        return

    send_message(profile.telegram_chat_id, "Jarayonni boshlash uchun /start bosing.")


def handle_admin_callback(callback_query: dict) -> None:
    callback_data = callback_query.get("data", "")
    callback_id = callback_query.get("id")

    if callback_data.startswith("admin:"):
        handle_admin_menu_callback(callback_query)
        return

    if callback_data.startswith("approve_payment:"):
        _, flow_id = callback_data.split(":")
        try:
            flow = OrderPaymentFlow.objects.select_related("telegram_profile", "order").get(id=flow_id)
        except OrderPaymentFlow.DoesNotExist:
            answer_callback_query(callback_id, "Flow topilmadi")
            return

        approve_payment(flow)
        answer_callback_query(callback_id, "Tasdiqlandi")
        return

    if callback_data.startswith("reject_payment:"):
        _, flow_id = callback_data.split(":")
        try:
            flow = OrderPaymentFlow.objects.select_related("telegram_profile", "order").get(id=flow_id)
        except OrderPaymentFlow.DoesNotExist:
            answer_callback_query(callback_id, "Flow topilmadi")
            return

        reject_payment(flow)
        answer_callback_query(callback_id, "Rad etildi")
        return


def process_update(update: dict) -> None:
    callback_query = update.get("callback_query")
    if callback_query:
        data = callback_query.get("data", "")
        if data.startswith("select_order:"):
            handle_order_selection(callback_query)
            return
        if data.startswith("approve_payment:") or data.startswith("reject_payment:") or data.startswith("admin:"):
            handle_admin_callback(callback_query)
            return

    message = update.get("message")
    if not message:
        return

    if message.get("contact"):
        handle_contact_message(message)
        return

    if message.get("location"):
        handle_location_message(message)
        return

    if message.get("photo"):
        handle_photo_message(message)
        return

    if message.get("text"):
        if handle_admin_text_message(message):
            return
        handle_text_message(message)
