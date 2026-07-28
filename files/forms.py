import logging
import os
from pathlib import PurePosixPath

from crispy_forms.helper import FormHelper
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction

from .models import File

try:
    import magic
except ImportError:
    magic = None

logger = logging.getLogger(__name__)


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ["file"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update({"class": "form-control"})
        self.helper = FormHelper()

    def clean_file(self):
        file_data = self.cleaned_data.get("file")
        if not file_data:
            return file_data

        # Detect MIME type from file contents, not the request header.
        if magic:
            detected_type = magic.from_buffer(file_data.read(2048), mime=True)
            file_data.seek(0)

            if detected_type not in settings.ALLOWED_TYPES:
                raise ValidationError("Unsupported file type.")

            self._detected_content_type = detected_type

        # Sanitize the filename: first, strip any path components.
        original_name = PurePosixPath(file_data.name or "upload").name
        safe_name = "".join(
            c for c in original_name if c.isalnum() or c in "._- "
        ).strip()
        self._sanitized_filename = safe_name or "upload"

        return file_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.request and self.request.user.is_authenticated:
            instance.owner = self.request.user

        if instance.file:
            instance.content_type = getattr(
                self, "_detected_content_type", "application/octet-stream"
            )
            instance.filename = getattr(self, "_sanitized_filename", instance.filename)

        if commit:
            # Atomic Transaction for File System hygiene
            try:
                with transaction.atomic():
                    instance.save()
            except DatabaseError:
                # If the DB save fails, check if the file was already written to disk.
                if instance.file and hasattr(instance.file, "path"):
                    try:
                        os.remove(instance.file.path)
                        logger.warning(
                            "DB transaction failed. Deleted orphan file: %s", instance.file.path
                        )
                    except FileNotFoundError:
                        pass

                # Inform the view that the save failed
                raise

        return instance
