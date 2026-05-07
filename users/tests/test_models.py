from django.db.utils import IntegrityError

from common.cases import BaseTestCase
from users.models import User

from . import PASSWORD
from .factories import UserFactory


class UserModelTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def test_instantiation(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password=PASSWORD
        )
        self.assertIsNotNone(user.pk)
        self.assertEqual(user.email, "test@example.com")

    def test_username_is_insensitive(self):
        """
        The username field is saved as lowercase to ensure case insensitivity.
        """
        user = UserFactory(username="TestUser")
        fetched_user = User.objects.get(username="testuser")
        self.assertEqual(user, fetched_user)

        with self.assertRaises(IntegrityError):
            UserFactory(username="testuser")

    def test_avatar_upload_path(self):
        user = UserFactory.create(username="testuser_avatar")
        filename = "myavatar.png"
        path = user._meta.get_field("avatar").upload_to(user, filename)
        self.assertEqual(path, f"avatars/{user.slug}/{filename}")
