from django.contrib import admin

from apps.telegram_bot.models import TelegramBotAdmin, BotSetting, BotAdminContact

# Register your models here.

admin.site.register(TelegramBotAdmin)
admin.site.register(BotSetting)
admin.site.register(BotAdminContact)