import os

from common.cases import BaseTestCase

from ..models import File
from .factories import FileFactory


class FileTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_file_instantiation(self):
        """This is a manual test to build a File instance and verify fields."""
        fname = "test_document.txt"
        inst = File.objects.create(
            owner=self.member,
            # create_test_file returns an InMemoryUploadedFile or SimpleUploadedFile
            file=self.create_test_file(name=fname),
        )

        self.assertIsNotNone(inst.pk)
        self.assertEqual(inst.owner, self.member)
        self.assertEqual(inst.filename, fname)

        # Verify the file exists on disk in the correct path
        # Path should be: SENDFILE_ROOT / user_id / filename
        # Since SENDFILE_ROOT is set to self.uploads_dir
        expected_path = os.path.join(self.uploads_dir, str(self.member.id), fname)
        self.assertTrue(
            os.path.exists(expected_path), f"File not found at {expected_path}"
        )

    def test_manager_by_owner(self):
        # Create files for member
        for _ in range(3):
            FileFactory.create(owner=self.member)

        # Create file for staff
        FileFactory.create(owner=self.staff)

        member_files = File.objects.by_owner(self.member)
        staff_files = File.objects.by_owner(self.staff)

        self.assertEqual(member_files.count(), 3)
        self.assertEqual(staff_files.count(), 1)
        self.assertTrue(all(f.owner == self.member for f in member_files))
        self.assertTrue(all(f.owner == self.staff for f in staff_files))

    def test_manager_public(self):
        # Create public files
        public_users = [self.member, self.staff]
        for user in public_users:
            for _ in range(2):
                FileFactory.create(owner=user)

        # Create private user and files
        for _ in range(2):
            FileFactory.create(owner=self.private)

        public_files = File.objects.public()

        self.assertEqual(public_files.count(), 4)
        self.assertTrue(all(f.owner.is_public for f in public_files))
