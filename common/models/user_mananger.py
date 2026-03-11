from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager

from django.core.validators import EmailValidator, RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon formati noto‘g‘ri. Masalan: +998901234567"
)

email_validator = EmailValidator(message="Email formati noto‘g‘ri.")


class CustomUserManager(BaseUserManager):
    def create_user(self, email: str, password=None, **extra_fields):
        if not email:
            raise ValueError("Email majburiy")
        email = self.normalize_email(email).strip().lower()
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            # OTP login bo‘lsa odatda unusable password
            user.set_unusable_password()

        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        if not password:
            raise ValueError("Superuser uchun password majburiy")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email=email, password=password, **extra_fields)
