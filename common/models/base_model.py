import uuid

from django.db import models
from django.utils import timezone


class BaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    objects = BaseManager()
    all_objects = models.Manager()

    def soft_delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.is_deleted = True
        self.save(using=using, update_fields=['deleted_at', 'is_deleted'])

    def restore(self, using=None):
        self.deleted_at = None
        self.is_deleted = False
        self.save(using=using, update_fields=['deleted_at', 'is_deleted'])

    class Meta:
        abstract = True
