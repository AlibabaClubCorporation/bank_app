from django.db.models.signals import pre_save
from django.dispatch import receiver


from .models import User


@receiver(pre_save, sender=User)
def set_full_name(sender, instance,  **kwargs):
    if not instance.full_name:
        instance.full_name = f'{instance.first_name} {instance.last_name}'