import random
import string

from django.db import models
from django.utils import timezone
from datetime import timedelta

from common.models.base_model import BaseModel
from common.validators.phone_validator import phone_validator


class PhoneOTP(BaseModel):
    """
    Har bir OTP so'rov uchun alohida yozuv.
    5 daqiqadan keyin expire bo'ladi, 3 ta noto'g'ri urinishdan keyin block.
    """
    phone = models.CharField(max_length=13, db_index=True, validators=[phone_validator])
    code = models.CharField(max_length=5)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP({self.phone}) — {'✓' if self.is_verified else '✗'}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_blocked(self) -> bool:
        return self.attempts >= 3

    @staticmethod
    def generate_code() -> str:
        return "".join(random.choices(string.digits, k=5))