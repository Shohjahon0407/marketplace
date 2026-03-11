import uuid

from django.db import models


class Gender(models.TextChoices):
    MAN = "man", "Man"
    WOMAN = "woman", "Woman"


class Status(models.TextChoices):
    IN_STOCK = "in_stock", "Bor"
    OUT_OF_STOCK = "out_of_stock", "Yo‘q"


class DeliveryMethod(models.TextChoices):
    PICKUP = "pickup", "Pickup"
    DELIVERY = "delivery", "Delivery"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    DELIVERED = "delivered", "Delivered"


def generate_sku():
    # Format: SKU-XXXXXXXX (8 uppercase hex chars from uuid4)
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"
