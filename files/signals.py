import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import File


@receiver(post_delete, sender=File)
def delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when corresponding `File` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
