from common.cases import BaseTestCase
from files.templatetags.filecount import file_count

from .factories import FileFactory


class FileCountTemplateTagTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.file = FileFactory.create(owner=self.staff)

    def test_file_count_anonymous(self):
        """file_count returns 0 for anonymous user"""
        user = None
        result = file_count(user)
        self.assertEqual(result, 0)

    def test_file_count_no_files(self):
        """file_count returns 0 for authenticated user with no files"""
        user = self.member
        result = file_count(user)
        self.assertEqual(result, 0)

    def test_file_count_with_files(self):
        """file_count returns correct count for authenticated user with files"""
        # Create some test files owned by the user
        for __ in range(5):
            FileFactory.create(owner=self.member)

        result = file_count(self.member)
        self.assertEqual(result, 5)
