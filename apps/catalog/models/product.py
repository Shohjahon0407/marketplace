import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q, F

from apps.catalog.models.category import Category
from common.enums.enums import generate_sku, Status
from common.models.base_model import BaseModel


class Product(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        db_index=True
    )
    discount_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))]
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_STOCK, db_index=True)
    sku = models.CharField(max_length=64, unique=True, default=generate_sku, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["price"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["status"]),
        ]
        CheckConstraint(
            condition=Q(discount_price__isnull=True) | Q(discount_price__lt=F("price")),
            name="product_discount_price_lt_price"
        ),

    def __str__(self):
        return f"{self.name} — SKU: {self.sku}"

    @property
    def discount_percent(self) -> int:
        if self.discount_price and self.price and self.discount_price < self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0


class ProductCount(BaseModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="detail")
    stock = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        constraints = [
            CheckConstraint(condition=Q(stock__gte=0), name="product_stock_gte_0"),
        ]


def product_image_path(instance, filename):
    return f"products/{instance.product_id}/{uuid.uuid4().hex}_{filename}"


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=product_image_path)

    class Meta:
        ordering = ["id"]
