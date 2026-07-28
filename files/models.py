import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from common.models import Timestamped

User = get_user_model()


class DynamicUserFilesStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        # We ignore the passed location to force it to use our settings
        super().__init__(location=None, base_url=base_url)
        self.default_location = os.path.join(settings.BASE_DIR, "user_files")

    @property
    def location(self):
        # This property is accessed whenever the storage needs to write/read
        return getattr(settings, "SENDFILE_ROOT", self.default_location)


def get_user_files_storage():
    return DynamicUserFilesStorage()


@deconstructible
class Uploads:
    def __call__(self, instance, filename):
        # Return path relative to the storage root (e.g. 1/myfile.txt)
        return os.path.join(str(instance.owner.id), os.path.basename(filename))


uploads_path = Uploads()


class FileManager(models.Manager):

    def by_owner(self, user):
        return self.get_queryset().filter(owner=user)

    def public(self):
        publics = User.objects.filter(is_public=True)
        return self.get_queryset().filter(owner__in=publics)


class File(Timestamped):
    """This holds a single user uploaded file"""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="files"
    )
    filename = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Original filename"),
    )
    content_type = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("MIME type of the file"),
    )
    file = models.FileField(upload_to=uploads_path, storage=get_user_files_storage)

    objects: FileManager = FileManager()

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)
