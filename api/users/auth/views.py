import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.models import PhoneOTP
from .serializers import SendOTPSerializer, VerifyOTPSerializer, PasswordLoginSerializer

# TODO: Eskizga ulanganda quyidagini yoqish:
# from .services.eskiz import eskiz_service

User = get_user_model()
logger = logging.getLogger(__name__)

RESEND_COOLDOWN_SECONDS = 60


def _get_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class SendOTPView(APIView):
    """
    POST /auth/send-otp/
    Body: { "phone": "+998901234567" }

    Agar telefon egasi admin/worker bo'lsa — OTP yubormasdan
    "password_required" qaytaradi.
    Oddiy user bo'lsa yoki yangi raqam bo'lsa — OTP yuboradi.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=SendOTPSerializer,
        tags=["Auth"],
    )
    def post(self, request):
        authenticated = False
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        # ── Admin/Worker tekshiruvi ──
        try:
            user = User.objects.get(phone=phone)
            if user:
                authenticated = True
            if user.is_password_auth:
                return Response(
                    {
                        "auth_method": "password",
                        "detail": "Parol bilan kiring.",
                    },
                    status=status.HTTP_200_OK,
                )
        except User.DoesNotExist:
            pass  # Yangi user — OTP yuboramiz

        # ── Spam himoyasi ──
        recent = PhoneOTP.objects.filter(
            phone=phone,
            created_at__gte=timezone.now() - timedelta(seconds=RESEND_COOLDOWN_SECONDS),
        ).first()

        if recent:
            wait = RESEND_COOLDOWN_SECONDS - (timezone.now() - recent.created_at).seconds
            return Response(
                {"detail": f"{wait} soniyadan keyin qayta urinib ko'ring."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # ── OTP yaratish ──
        code = PhoneOTP.generate_code()
        PhoneOTP.objects.create(phone=phone, code=code)

        # TODO: Eskizga ulanganda quyidagini yoqish:
        # try:
        #     eskiz_service.send_otp(phone, code)
        # except Exception:
        #     logger.exception("SMS yuborishda xatolik: phone=%s", phone)
        #     return Response(
        #         {"detail": "SMS yuborishda xatolik yuz berdi."},
        #         status=status.HTTP_502_BAD_GATEWAY,
        #     )

        return Response(
            {
                "auth_method": "otp",
                "detail": "Tasdiqlash kodi yuborildi.",
                "code": code,  # TODO: Productionda olib tashlash!
                "authenticated": authenticated
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    POST /auth/verify-otp/
    Body: { "phone": "+998901234567", "code": "12345" }

    OTP tekshiradi → user bor bo'lsa login, yo'q bo'lsa register.
    Admin/Worker bu endpointdan foydalana olmaydi.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        tags=["Auth"],
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        # ── Admin/Worker OTP ishlatishi mumkin emas ──
        try:
            existing = User.objects.get(phone=phone)
            if existing.is_password_auth:
                return Response(
                    {"detail": "Siz parol bilan kirishingiz kerak."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except User.DoesNotExist:
            pass

        # ── Oxirgi faol OTP ──
        otp = PhoneOTP.objects.filter(
            phone=phone,
            is_verified=False,
        ).order_by("-created_at").first()

        if not otp:
            return Response(
                {"detail": "Avval OTP so'rang."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.is_expired:
            return Response(
                {"detail": "Kod muddati tugagan. Yangi kod so'rang."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.is_blocked:
            return Response(
                {"detail": "Urinishlar soni tugadi. Yangi kod so'rang."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if otp.code != code:
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            remaining = 3 - otp.attempts
            return Response(
                {"detail": "Kod noto'g'ri.", "remaining_attempts": max(remaining, 0)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── OTP tasdiqlandi ──
        otp.is_verified = True
        otp.save(update_fields=["is_verified"])

        # ── User: get or create ──
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"password": ""},
        )

        if not user.is_active:
            return Response(
                {"detail": "Akkaunt bloklangan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "detail": "Muvaffaqiyatli kirish." if not created else "Ro'yxatdan o'tdingiz.",
                "is_new_user": created,
                "tokens": _get_tokens(user),
            },
            status=status.HTTP_200_OK,
        )


class PasswordLoginView(APIView):
    """
    POST /auth/password-login/
    Body: { "phone": "+998901234567", "password": "secret" }

    Faqat admin (is_staff) va worker (is_worker) uchun.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordLoginSerializer,
        tags=["Auth"],
    )
    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"detail": "Telefon raqami yoki parol noto'g'ri."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ── Faqat admin/worker parol bilan kira oladi ──
        if not user.is_password_auth:
            return Response(
                {"detail": "Siz OTP orqali kirishingiz kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Telefon raqami yoki parol noto'g'ri."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Akkaunt bloklangan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "detail": "Muvaffaqiyatli kirish.",
                "tokens": _get_tokens(user),
            },
            status=status.HTTP_200_OK,
        )
