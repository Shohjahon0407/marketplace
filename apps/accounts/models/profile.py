from django.db import models

from common.enums.enums import Gender
from common.models.base_model import BaseModel
from config import settings


class Profile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    gender = models.CharField(
        max_length=10,
        choices=
        Gender.choices,
        blank=True,
        null=True,
    )
    birth_date = models.DateTimeField()
