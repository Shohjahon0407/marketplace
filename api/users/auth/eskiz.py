import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EskizSMSService:
    """
    Eskiz.uz SMS API wrapper.

    settings.py da quyidagilar kerak:
        ESKIZ_EMAIL = "your@email.com"
        ESKIZ_PASSWORD = "your_password"
        ESKIZ_BASE_URL = "https://notify.eskiz.uz/api"   # default
        ESKIZ_SENDER = "4546"                             # default sender id
    """

    def __init__(self):
        self.base_url = getattr(settings, "ESKIZ_BASE_URL", "https://notify.eskiz.uz/api")
        self.email = settings.ESKIZ_EMAIL
        self.password = settings.ESKIZ_PASSWORD
        self.sender = getattr(settings, "ESKIZ_SENDER", "4546")
        self._token: str | None = None

    # ── Token ───────────────────────────────────────────────
    def _get_token(self) -> str:
        """Eskiz auth token olish. Keshlab qo'yish mumkin (Redis/cache)."""
        if self._token:
            return self._token

        resp = requests.post(
            f"{self.base_url}/auth/login",
            data={"email": self.email, "password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        self._token = resp.json()["data"]["token"]
        return self._token

    # ── SMS yuborish ────────────────────────────────────────
    def send_sms(self, phone: str, message: str) -> dict:
        """
        SMS yuborish.
        phone: 998XXXXXXXXX formatda (+ belgisiz, 12 raqam).
        """
        token = self._get_token()

        # Eskiz + belgisiz kutadi, agar bor bo'lsa olib tashlaymiz
        clean_phone = phone.lstrip("+")

        payload = {
            "mobile_phone": clean_phone,
            "message": message,
            "from": self.sender,
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = requests.post(
                f"{self.base_url}/message/sms/send",
                data=payload,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("SMS yuborildi: phone=%s, status=%s", phone, data.get("status"))
            return data

        except requests.exceptions.HTTPError as e:
            # Token expire bo'lgan bo'lishi mumkin — bir marta retry
            if e.response is not None and e.response.status_code == 401:
                logger.warning("Eskiz token expired, refreshing...")
                self._token = None
                return self.send_sms(phone, message)
            logger.error("Eskiz SMS xato: %s", e)
            raise

    # ── OTP yuborish (convenience) ──────────────────────────
    def send_otp(self, phone: str, code: str) -> dict:
        message = f"Tasdiqlash kodi: {code}\nKodni hech kimga bermang."
        return self.send_sms(phone, message)


# Singleton instance — importda foydalaning
eskiz_service = EskizSMSService()