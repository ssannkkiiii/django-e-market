from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models

@receiver(post_save, sender=models.User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a Profile instance whenever a new User is created
    """
    if created:
        models.Profile.objects.create(user=instance)
