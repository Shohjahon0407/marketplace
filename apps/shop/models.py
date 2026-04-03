from django.db import models


class Shop(models.Model):
    shop_name = models.CharField(max_length=255, blank=True, default="Mening do'konim")
    order_fee = models.PositiveIntegerField(blank=True)
    shop_address = models.CharField(max_length=255, blank=True, null=True)
