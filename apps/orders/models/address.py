from django.db import models
from django.db.models import Q, UniqueConstraint

from apps.accounts.models import User
from common.models.base_model import BaseModel


class Address(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=80, default="Uy")
    region = models.CharField(max_length=80, blank=True)  # ixtiyoriy
    city = models.CharField(max_length=80, blank=True)
    street = models.CharField(max_length=120)
    house = models.CharField(max_length=30, blank=True)
    apartment = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False, db_index=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="uniq_default_address_per_user"
            ),
        ]

    def __str__(self):
        return f"{self.user_id}: {self.street} {self.house}".strip()
