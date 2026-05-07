from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import ShortUUIDField

from common.models import Timestamped


def avatar_upload_to(instance, filename):
    return "avatars/{}/{}".format(instance.slug, filename)


class User(Timestamped, AbstractUser):
    """Our custom User model"""

    slug = ShortUUIDField()
    public_name = models.CharField(
        max_length=150, blank=True, help_text=_("Publicly visible name")
    )
    about = models.TextField(blank=True, help_text=_("Write something about yourself"))
    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        blank=True,
        null=True,
        help_text=_("Upload an image to personalize your profile"),
    )
    is_public = models.BooleanField(
        default=True,
        help_text=_("Is this profile visible to others? Can they publish files? "),
    )

    def best_name(self) -> str:
        """Return the best public name to display for this user."""
        if self.public_name:
            return self.public_name
        return "Filebaby-{}".format(self.pk)

    def clean(self):
        if self.username:
            self.username = self.username.lower()
        super().clean()

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower()

        if self.pk:
            try:
                old = self.__class__.objects.get(pk=self.pk)
                if old.avatar and old.avatar != self.avatar:
                    old.avatar.delete(save=False)
            except self.__class__.DoesNotExist:
                pass

        super().save(*args, **kwargs)
