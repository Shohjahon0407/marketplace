from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):

    def create_user(self, phone: str, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqami majburiy")

        extra_fields.setdefault("is_active", True)
        user = self.model(phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone: str, password: str, **extra_fields):
        if not password:
            raise ValueError("Superuser uchun password majburiy")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_worker", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(phone=phone, password=password, **extra_fields)
