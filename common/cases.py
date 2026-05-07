import os
import tempfile
import uuid
from io import BytesIO
from shutil import rmtree

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from users.tests.factories import UserFactory


class ImageMixin(object):
    def create_image(
        self, width=150, height=150, mode="RGBA", color="#E0E04C"
    ) -> Image.Image:
        """
        Create a new PIL Image.

        @param height height of the image in pixels
        @param width Width of the image in pixels
        @param mode Type of image (ie. "RGB", "RGBA", "L", etc)
        @param color Image fill color in hex (ie. "#E0E04C"),
                     None or 0 returns uninitialized Image

        @return: PIL Image
        @rtype: Image
        """
        return Image.new(mode=mode, size=(width, height), color=color)

    def create_image_as_bytesio(self, name=None, image=None):
        if image is None:
            image = self.create_image()

        if name is None:
            name = "{}.png".format(str(uuid.uuid4()))

        bytes_storage = BytesIO()
        image.save(bytes_storage, format="PNG")
        bytes_storage.seek(0)
        bytes_storage.name = name
        return bytes_storage

    def create_image_as_bytes(self, name=None, image=None):
        bytes_storage = self.create_image_as_bytesio(name, image)
        image_bytes = bytes_storage.getvalue()
        return image_bytes

    def get_uploaded_file(
        self, name=None, content=None, content_type="image/png", image=None
    ):
        """
        Creates a SimpleUploadedFile containing a PNG image

        @param name is a string
        @param content is a byte array (ie. b"some-bytes")
        @param content_type is an IANA media type string (ie. text/plain)
        @param image is a PIL Image instance or None to create a default image

        @return SimpleUploadedFile instance
        """
        if name is None:
            name = "{}.png".format(str(uuid.uuid4()))

        if content is None:
            content = self.create_image_as_bytes(name, image)

        up = SimpleUploadedFile(name, content, content_type)
        return up


class BaseTestCase(ImageMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.uploads_dir = tempfile.mkdtemp()
        self._override_uploads = override_settings(SENDFILE_ROOT=self.uploads_dir)
        self._override_uploads.enable()

        self.media_dir = tempfile.mkdtemp()
        self._override_media = override_settings(MEDIA_ROOT=self.media_dir)
        self._override_media.enable()
        self.member = UserFactory()
        self.another = UserFactory(username="another_member")
        self.private = UserFactory(is_public=False)
        self.admin = UserFactory(username="admin", is_staff=True, is_superuser=True)
        self.staff = UserFactory(username="staff", is_staff=True, is_superuser=False)

    def tearDown(self):
        if self.uploads_dir and os.path.exists(self.uploads_dir):
            self._override_uploads.disable()
            rmtree(self.uploads_dir, ignore_errors=True)

        if self.media_dir and os.path.exists(self.media_dir):
            self._override_media.disable()
            rmtree(self.media_dir, ignore_errors=True)

        super().tearDown()

    def create_test_file(self, name=None, content=None, content_type="text/plain"):
        """
        Helper method to create a text file for testing.

        @param name: Name of the file.
        @param content: Content of the file. If None, default content is used.
        @return: SimpleUploadedFile instance.
        """

        if name is None:
            name = "test_file.txt"
        if content is None:
            content = b"Sample text content."

        return SimpleUploadedFile(name, content, content_type=content_type)

    def debugform(self, form):
        print("Form.is_valid() is {}".format(form.is_valid()))
        if not form.is_valid():
            print("Form.errors: {}".format(form.errors))

    def mute(self):
        import logging

        logging.disable(logging.CRITICAL)  # Shaddap

    def unmute(self):
        import logging

        logging.disable(logging.NOTSET)
