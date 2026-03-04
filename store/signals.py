from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomerProfile

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        # Only create if not already present (for safety)
        CustomerProfile.objects.get_or_create(
            user=instance,
            defaults={
                "email": instance.email,
                "first_name": instance.first_name or "",
                "last_name": instance.last_name or "",
            }
        )