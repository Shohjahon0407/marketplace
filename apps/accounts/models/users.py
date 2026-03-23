from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from common.models.base_model import BaseModel
from common.models.user_mananger import CustomUserManager
from common.validators.phone_validator import phone_validator


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Passwordless phone OTP auth.
    Admin/Worker foydalanuvchilar parol bilan kiradi.
    Oddiy userlar faqat OTP bilan kiradi.
    """
    phone = models.CharField(
        max_length=13,
        unique=True,
        db_index=True,
        validators=[phone_validator],
    )
    password = models.CharField(max_length=255, blank=True)

    name = models.CharField(max_length=120, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_worker = models.BooleanField(default=False)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.phone

    @property
    def is_password_auth(self) -> bool:
        """Admin yoki worker bo'lsa — parol bilan kiradi."""
        return self.is_staff or self.is_worker
