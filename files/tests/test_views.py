import os
from typing import Any
from unittest import skipIf
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.urls import reverse

from common.cases import BaseTestCase
from files.models import File
from files.tests.factories import FileFactory

from . import DATA_DIR

try:
    import magic
except ImportError:
    magic = None


class FileCreateViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("files:create")

    def test_file_create_get(self):
        """Test the file creation page loads for an authenticated user."""
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "files/file_form.html")

    def test_file_create_protected(self):
        """Test that unauthenticated users cannot access the file upload view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")

    def test_file_create_post_success(self):
        """Test that a file can be successfully uploaded."""
        File.objects.all().delete()
        self.client.force_login(self.member)
        response = self.client.post(
            self.url, {"file": self.create_test_file()}, follow=True
        )

        self.assertRedirects(response, reverse("files:list"))

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "File uploaded successfully")

        # Check file was created in DB
        self.assertEqual(File.objects.count(), 1)
        file_obj = File.objects.get()
        self.assertEqual(file_obj.owner, self.member)
        self.assertEqual(file_obj.filename, "test_file.txt")
        if magic:
            self.assertEqual(file_obj.content_type, "text/plain")

    def test_file_create_post_empty(self):
        """Test that posting an empty form fails."""
        self.client.force_login(self.member)
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("file", form.errors)
        self.assertEqual(form.errors["file"], ["This field is required."])
        self.assertEqual(File.objects.count(), 0)

    @skipIf(magic is None, "magic library is not available")
    def test_invalid_file_content_type_returns_json_for_dropzone(self):
        """Dropzone uploads with unsupported MIME should return a JSON 400 error"""
        self.client.force_login(self.member)

        with open(os.path.join(DATA_DIR, "tiny.tif"), "rb") as f:
            data = f.read()

        self.mute()
        response = self.client.post(
            self.url,
            {
                "file": self.create_test_file(
                    name="tiny.tif", content=data, content_type="image/tiff"
                )
            },
            HTTP_X_REQUESTED_BY="Dropzone",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Unsupported file type."})
        self.assertEqual(File.objects.count(), 0)

    @skipIf(magic is None, "magic library is not available")
    def test_invalid_file_content_type_renders_form_errors(self):
        """Invalid uploads should render the form with field errors"""
        self.client.force_login(self.member)

        with open(os.path.join(DATA_DIR, "tiny.tif"), "rb") as f:
            data = f.read()

        self.mute()
        response = self.client.post(
            self.url,
            {
                "file": self.create_test_file(
                    name="tiny.tif", content=data, content_type="image/tiff"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("file", form.errors)
        self.assertIn("Unsupported file type.", form.errors["file"])
        self.assertEqual(File.objects.count(), 0)

    @patch("files.forms.magic", None)
    @patch("files.views.FileForm.save", side_effect=IntegrityError("forced db failure"))
    def test_upload_db_failure_returns_json_for_dropzone(self, mock_form_save):
        """Dropzone uploads should receive JSON error when DB save fails"""
        self.client.force_login(self.member)

        response = self.client.post(
            self.url,
            {"file": self.create_test_file(name="db_failure.txt")},
            HTTP_X_REQUESTED_BY="Dropzone",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Upload failed. Please try again."})
        self.assertEqual(File.objects.count(), 0)
        self.assertTrue(mock_form_save.called)

    @patch("files.forms.magic", None)
    @patch("files.views.FileForm.save", side_effect=IntegrityError("forced db failure"))
    def test_upload_db_failure_renders_form_error_without_dropzone(
        self, mock_form_save
    ):
        """Render form errors when DB save fails"""
        self.client.force_login(self.member)

        response = self.client.post(
            self.url,
            {"file": self.create_test_file(name="db_failure.txt")},
        )

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("file", form.errors)
        self.assertIn("Upload failed. Please try again.", form.errors["file"])
        self.assertEqual(File.objects.count(), 0)
        self.assertTrue(mock_form_save.called)


class FileListViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("files:list")

    def test_file_list_get(self):
        """Test the file list view for an authenticated user."""
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "files/file_list.html")

    def test_get_queryset_no_slug_yields_public_users_files(self):
        """
        If there is no slug then it yields Files that are owned by users who have is_public
        set to True.
        """
        # Create file for member (public default)
        file1 = FileFactory.create(
            owner=self.member,
            file=self.create_test_file("member_file.txt", b"member content"),
        )
        # Create file for private user
        file2 = FileFactory.create(
            owner=self.private,
            file=self.create_test_file("private_file.txt", b"private content"),
        )

        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(file1, response.context["files"])
        self.assertNotIn(file2, response.context["files"])

    def test_get_queryset_with_slug_yields_specific_public_user_files(self):
        """A slug if set yields Files owned by a specific public user"""
        # Create file for member (public)
        file1 = FileFactory.create(
            owner=self.member,
            file=self.create_test_file("member_file.txt", b"member content"),
        )
        # Create file for staff (also public)
        file2 = FileFactory.create(
            owner=self.staff,
            file=self.create_test_file("staff_file.txt", b"staff content"),
        )

        url = reverse("files:list_from", kwargs={"slug": self.member.slug})
        self.client.force_login(self.member)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(file1, response.context["files"])
        self.assertNotIn(file2, response.context["files"])

    def test_get_queryset_with_slug_for_private_user(self):
        """Private users can see their own files when accessed with their slug."""
        # Create file for member (public)
        file1 = FileFactory.create(
            owner=self.private,
            file=self.create_test_file(),
        )
        url = reverse("files:list_from", kwargs={"slug": self.private.slug})
        self.client.force_login(self.private)
        self.mute()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(file1, response.context["files"])

    def test_get_queryset_with_slug_returns_404_if_user_not_public(self):
        """It returns Http 404 if the user slug is not public."""
        url = reverse("files:list_from", kwargs={"slug": self.private.slug})
        self.client.force_login(self.member)
        self.mute()
        response = self.client.get(url)
        self.unmute()
        self.assertEqual(response.status_code, 404)

    def test_get_queryset_with_slug_returns_404_if_user_does_not_exist(self):
        """It returns Http 404 if the user slug does not exist."""
        # Using a valid looking but non-existent slug to be safe, though non-matching string is fine too
        url = reverse("files:list_from", kwargs={"slug": "non-existent-slug"})
        self.client.force_login(self.member)
        self.mute()
        response = self.client.get(url)
        self.unmute()
        self.assertEqual(response.status_code, 404)

    def test_file_list_pagination(self):
        """Test that the file list is paginated correctly."""
        # Create 14 files for member
        for i in range(14):
            FileFactory.create(owner=self.member)

        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["files"]), 5)

        response = self.client.get(self.url + "?page=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["files"]), 4)


class FileDetailViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.file = FileFactory.create(owner=self.member)
        self.url = reverse("files:detail", args=[self.file.pk])

    def test_file_detail_get(self):
        """Test the file detail page loads for the public."""
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "files/file_detail.html")
        self.assertEqual(response.context["object"], self.file)

        self.client.force_login(self.private)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_private_file_detail_by_owner(self):
        """Test that the owner of a private file can view its detail page."""
        self.file = FileFactory.create(owner=self.private)
        self.client.force_login(self.private)
        response = self.client.get(reverse("files:detail", args=[self.file.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["object"], self.file)

    def test_file_detail_access_denied_for_private_user(self):
        """
        Test that a user cannot view the file details of a private user's file.
        """
        self.file = FileFactory.create(owner=self.private)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("files:detail", args=[self.file.pk]))
        # Should be 404 because get_queryset filters by owner privacy
        self.assertEqual(response.status_code, 404)

    def test_file_detail_protected(self):
        """Test that unauthenticated users cannot access the detail view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")


class FileDeleteViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.file = FileFactory.create(owner=self.member)
        self.url = reverse("files:delete", args=[self.file.pk])

    def test_file_delete_get(self):
        """Test the file delete confirmation page loads."""
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "files/file_confirm_delete.html")

    def test_file_delete_post_success(self):
        """Test that a file can be successfully deleted."""
        self.client.force_login(self.member)

        # Verify file exists before delete
        file_path = self.file.file.path
        self.assertTrue(os.path.exists(file_path))

        response = self.client.post(self.url, follow=True)

        self.assertRedirects(response, reverse("files:list"))

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "File deleted successfully")

        # Check file was deleted from DB
        self.assertEqual(File.objects.count(), 0)

        # Check if the file was deleted from disk
        # Note: Django's default FileSystemStorage behaviour does NOT delete files when models are deleted,
        self.assertFalse(os.path.exists(file_path))

    def test_file_delete_protected(self):
        """Test that unauthenticated users cannot access the delete view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")


class FileDownloadViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.file = FileFactory.create(owner=self.member)
        self.url = reverse("files:download", args=[self.file.pk])

    def test_file_download_get(self):
        """Test the file downloads work for the owner and others."""
        self.client.force_login(self.member)
        response: Any = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # FileResponse is a StreamingHttpResponse, so we must consume streaming_content
        content = b"".join(response.streaming_content)
        self.assertEqual(content, b"TEST")
        self.assertEqual(response["Content-Type"], "text/plain")

        self.client.force_login(self.private)  # Private users can download too
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_file_download_access_denied_for_private_users(self):
        """Test that another user cannot download the file of a private user."""
        self.client.force_login(self.another)
        self.file.owner = self.private
        self.file.save()
        response = self.client.get(self.url)
        # Should be 404 because get_queryset filters by public owner
        self.assertEqual(response.status_code, 404)

    def test_private_file_download_by_owner(self):
        """Test that the owner of a private file can download it."""
        self.client.force_login(self.private)
        self.file.owner = self.private
        self.file.save()
        response = self.client.get(self.url)
        # Should be 200 b/c its your own file
        self.assertEqual(response.status_code, 200)

    def test_staff_can_download_any_file(self):
        """Test that staff users can download any file."""
        self.client.force_login(self.staff)
        self.file.owner = self.private
        self.file.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_file_download_protected(self):
        """Test that unauthenticated users cannot access the download view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")
