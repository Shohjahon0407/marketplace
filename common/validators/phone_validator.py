from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+?\d{7,15}$",
    message="Telefon raqam noto‘g‘ri formatda. Masalan: +998901234567"
)
