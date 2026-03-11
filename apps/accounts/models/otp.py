from __future__ import annotations

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from common.models.base_model import BaseModel
from common.models.user_mananger import email_validator, phone_validator


class OTPCode(BaseModel):
    """
    Universal OTP:
    - channel=email bo‘lsa target=email
    - channel=phone bo‘lsa target=phone
    OTP ni plaintext saqlama. Hash saqla.
    """

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"

    channel = models.CharField(max_length=10, choices=Channel.choices, db_index=True)
    target = models.CharField(max_length=128, db_index=True)  # email yoki phone string

    code_hash = models.CharField(max_length=128)  # make_password natijasi
    expires_at = models.DateTimeField(db_index=True)

    # Anti-bruteforce:
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    # Anti-spam:
    sent_count_day = models.PositiveSmallIntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    is_used = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["channel", "target", "-created_at"]),
            models.Index(fields=["channel", "target", "is_used", "-created_at"]),
        ]

    def clean(self):
        # Model-level validation (serializerda ham tekshir, lekin bu ham foydali)
        if self.channel == self.Channel.EMAIL:
            email_validator(self.target)
            self.target = self.target.strip().lower()
        elif self.channel == self.Channel.PHONE:
            phone_validator(self.target)
        else:
            raise ValidationError({"channel": "Noto‘g‘ri channel"})

    @classmethod
    def make(cls, channel: str, target: str, code: str, ttl_seconds: int = 120) -> "OTPCode":
        obj = cls(
            channel=channel,
            target=target,
            code_hash=make_password(code),
            expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
        )
        obj.full_clean()
        return obj

    def verify(self, code: str) -> bool:
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        if self.attempts >= self.max_attempts:
            return False

        ok = check_password(code, self.code_hash)
        self.attempts += 1
        if ok:
            self.is_used = True
        self.save(update_fields=["attempts", "is_used", "updated_at"])
        return ok
