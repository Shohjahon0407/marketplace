from django.urls import path

from api.users.auth.views import SendOTPView, VerifyOTPView, PasswordLoginView

urlpatterns = [
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("password-login/", PasswordLoginView.as_view(), name="password-login"),
]