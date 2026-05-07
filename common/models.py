from django.db import models
from django.utils import timezone


class Timestamped(models.Model):
    """
    Some important timestamps for objects

    From Mezzanine CMS
    """

    created = models.DateTimeField(null=True, editable=False)
    updated = models.DateTimeField(null=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        when = kwargs.pop("when", timezone.now())
        self.updated = when
        if not self.pk:
            self.created = when
        return super().save(*args, **kwargs)
