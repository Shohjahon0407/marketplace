# api/auth/utils.py
import secrets
import string
from django.conf import settings
from django.core.mail import send_mail

def generate_6_digit_code() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))

def send_otp_email(to_email: str, code: str, ttl_minutes: int = 5):
    subject = "Login code"
    message = (
        f"Your one-time code: {code}\n"
        f"Expires in {ttl_minutes} minutes."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    send_mail(subject, message, from_email, [to_email], fail_silently=False)