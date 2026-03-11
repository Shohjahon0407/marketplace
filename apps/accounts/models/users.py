from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from common.models.base_model import BaseModel
from common.models.user_mananger import email_validator, CustomUserManager
from common.validators.phone_validator import phone_validator


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Devda email OTP bilan ishlatamiz.
    Keyin phone OTP qo‘shsang ham user modelni sindirmaysan: phone maydoni allaqachon bor.
    """
    email = models.EmailField(unique=True, db_index=True, validators=[email_validator])
    password = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        validators=[phone_validator],
    )

    name = models.CharField(max_length=120, blank=True)

    is_active = models.BooleanField(default=True)

    # Django admin
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
