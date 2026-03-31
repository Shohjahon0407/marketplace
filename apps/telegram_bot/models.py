from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.orders.models import Order
from common.models.base_model import BaseModel
from common.enums.telegram_bot import TelegramUserState, TelegramAdminState, PaymentFlowStatus


class TelegramProfile(BaseModel):
    telegram_user_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_chat_id = models.BigIntegerField(db_index=True)
    username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    state = models.CharField(
        max_length=50,
        choices=TelegramUserState.choices,
        default=TelegramUserState.IDLE,
        db_index=True,
    )

    selected_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telegram_selected_profiles",
    )

    def __str__(self):
        return f"{self.telegram_user_id} - {self.username or self.first_name}"


class TelegramBotAdmin(BaseModel):
    telegram_user_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_chat_id = models.BigIntegerField(db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    state = models.CharField(
        max_length=50,
        choices=TelegramAdminState.choices,
        default=TelegramAdminState.IDLE,
        db_index=True,
    )

    temp_full_name = models.CharField(max_length=255, blank=True)
    temp_username = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.full_name or str(self.telegram_user_id)


class BotSetting(BaseModel):
    payment_card_number = models.CharField(max_length=64, blank=True)
    payment_card_owner = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Bot settings"


class BotAdminContact(BaseModel):
    full_name = models.CharField(max_length=255)
    telegram_username = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class OrderPaymentFlow(BaseModel):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="telegram_payment_flow",
    )
    telegram_profile = models.ForeignKey(
        TelegramProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_flows",
    )

    status = models.CharField(
        max_length=50,
        choices=PaymentFlowStatus.choices,
        default=PaymentFlowStatus.SELECTING_ORDER,
        db_index=True,
    )

    amount_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    card_number_snapshot = models.CharField(max_length=64, blank=True)
    card_owner_snapshot = models.CharField(max_length=255, blank=True)

    receipt_file_id = models.CharField(max_length=255, blank=True)
    receipt_uploaded_at = models.DateTimeField(null=True, blank=True)

    location_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_uploaded_at = models.DateTimeField(null=True, blank=True)

    admin_note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.order.order_code} - {self.status}"