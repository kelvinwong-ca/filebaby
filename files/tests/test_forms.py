import os
from unittest import skipIf
from unittest.mock import Mock, patch

from django.core.files.base import ContentFile
from django.db import IntegrityError

from common.cases import BaseTestCase

from ..forms import FileForm
from . import DATA_DIR

try:
    import magic
except ImportError:
    magic = None


class FileFormTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.form_class = FileForm

    def test_file_form_valid(self):
        """Test that the FileForm is valid with proper data."""
        form_data = {}
        form_files = {
            "file": self.create_test_file(),
        }
        form = self.form_class(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

    @skipIf(magic is None, "magic library is not available")
    def test_file_form_save_filename(self):
        """Test that the filename is automatically populated on save."""
        with open(os.path.join(DATA_DIR, "test.pdf"), "rb") as f:
            data = f.read()

        form_data = {}
        test_file = self.create_test_file(
            name="my_document.pdf", content=data, content_type="application/pdf"
        )
        form_files = {
            "file": test_file,
        }

        # Mock request with user
        request = Mock()
        request.user = self.member

        form = self.form_class(data=form_data, files=form_files, request=request)
        self.assertTrue(form.is_valid())

        instance = form.save()
        self.assertEqual(instance.filename, "my_document.pdf")
        self.assertEqual(instance.content_type, "application/pdf")
        self.assertEqual(instance.owner, self.member)

    def test_file_form_invalid_missing_file(self):
        """Test that the FileForm is invalid when the file is missing."""
        form_data = {}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    @skipIf(magic is None, "magic library is not available")
    @patch("files.forms.magic.from_buffer", return_value="application/octet-stream")
    def test_file_form_invalid_unsupported_mime(self, mock_from_buffer):
        """Test that unsupported MIME type fails form validation."""
        form_data = {}
        form_files = {
            "file": self.create_test_file(
                name="payload.bin", content=b"binary payload"
            ),
        }

        form = self.form_class(data=form_data, files=form_files)

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
        self.assertIn("Unsupported file type.", form.errors["file"])
        self.assertTrue(mock_from_buffer.called)

    @patch("files.forms.magic", None)
    def test_form_fallback_without_magic(self):
        """Test that form validation works without the magic library."""
        form_data = {}
        form_files = {
            "file": self.create_test_file(
                name="test.txt", content=b"Hello, world!", content_type="text/plain"
            ),
        }
        # Mock request with user
        request = Mock()
        request.user = self.member

        form = self.form_class(data=form_data, files=form_files, request=request)

        self.assertTrue(form.is_valid())

        instance = form.save()
        self.assertEqual(instance.filename, "test.txt")
        self.assertEqual(instance.content_type, "application/octet-stream")

    @patch("files.forms.magic", None)
    @patch("files.forms.File.save", autospec=True)
    def test_form_save_removes_orphan_file_on_save_failure(self, mock_model_save):
        """Test that save failure cleans up any file written before DB rollback."""

        def _fail_after_writing_file(instance, *args, **kwargs):
            # Simulate storage write before a DB error happens.
            stored_name = instance.file.storage.save(
                instance.file.name, ContentFile(b"orphan content")
            )
            instance.file.name = stored_name
            raise IntegrityError("forced db failure")

        mock_model_save.side_effect = _fail_after_writing_file

        request = Mock()
        request.user = self.member

        form = self.form_class(
            data={},
            files={"file": self.create_test_file(name="orphan.txt")},
            request=request,
        )
        self.assertTrue(form.is_valid())

        with self.assertRaises(IntegrityError):
            self.mute()
            form.save()

        self.assertFalse(os.path.exists(form.instance.file.path))
