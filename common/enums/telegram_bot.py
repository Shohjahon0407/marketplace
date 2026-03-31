from django.db import models


class TelegramUserState(models.TextChoices):
    IDLE = "idle", "Idle"
    WAIT_PHONE = "wait_phone", "Wait phone"
    WAIT_RECEIPT = "wait_receipt", "Wait receipt"
    WAIT_LOCATION = "wait_location", "Wait location"
    DONE = "done", "Done"


class TelegramAdminState(models.TextChoices):
    IDLE = "idle", "Idle"
    WAIT_CARD_NUMBER = "wait_card_number", "Wait card number"
    WAIT_CARD_OWNER = "wait_card_owner", "Wait card owner"
    WAIT_CONTACT_NAME = "wait_contact_name", "Wait contact name"
    WAIT_CONTACT_USERNAME = "wait_contact_username", "Wait contact username"
    WAIT_CONTACT_PHONE = "wait_contact_phone", "Wait contact phone"


class PaymentFlowStatus(models.TextChoices):
    SELECTING_ORDER = "selecting_order", "Selecting order"
    WAITING_RECEIPT = "waiting_receipt", "Waiting receipt"
    RECEIPT_UPLOADED = "receipt_uploaded", "Receipt uploaded"
    LOCATION_UPLOADED = "location_uploaded", "Location uploaded"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"