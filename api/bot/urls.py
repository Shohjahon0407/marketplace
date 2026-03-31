from django.urls import path

from api.bot.views import TelegramWebhookAPIView

urlpatterns = [
    path("telegram/webhook/", TelegramWebhookAPIView.as_view(), name="telegram-webhook"),
]
