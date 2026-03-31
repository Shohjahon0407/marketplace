from django.urls import path

from api.order_bot.views import TelegramWebhookAPIView

urlpatterns = [
    path("webhook/<str:secret>/", TelegramWebhookAPIView.as_view(), name="telegram-webhook"),
]