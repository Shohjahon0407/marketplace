from decimal import Decimal
from django.conf import settings
from django.db import models, transaction, IntegrityError

from common.enums.code_generators.order_code import generate_order_code
from common.enums.enums import OrderStatus, DeliveryMethod
from common.models.base_model import BaseModel
from apps.catalog.models.product import Product


class Order(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    order_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    delivery_method = models.CharField(
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.PICKUP
    )

    delivery_address = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    comment = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.order_code:
            return super().save(*args, **kwargs)

        for _ in range(10):
            self.order_code = generate_order_code()
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError:
                self.order_code = ""

        raise IntegrityError("Unique order_code yaratib bo'lmadi.")

    def __str__(self):
        return f"{self.order_code} - {self.user}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")

    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
