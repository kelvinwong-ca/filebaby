import os

import factory

from files.models import File
from users.tests.factories import UserFactory

from . import TEST_DIR


class FileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = File

    owner = factory.SubFactory(UserFactory)
    file = factory.django.FileField(
        from_path=os.path.join(TEST_DIR, "data", "test_file.txt")
    )
    content_type = "text/plain"
