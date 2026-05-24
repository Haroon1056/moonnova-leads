from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserUsage


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_usage(sender, instance, created, **kwargs):
    """
    Create usage limits automatically when a new user registers.
    """

    if created:
        UserUsage.objects.create(user=instance)