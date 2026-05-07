from common.cases import BaseTestCase

from ..forms import CreateUserForm, UpdateUserForm
from . import PASSWORD
from .factories import UserFactory


class CreateUserFormTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }

    def test_instantiation(self):
        form = CreateUserForm(data=self.user_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        data = {}
        form = CreateUserForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertIn("password1", form.errors)

    def test_password_mismatch(self):
        self.user_data["password2"] = "mismatch"
        form = CreateUserForm(data=self.user_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_existing_username(self):
        UserFactory(username=self.user_data["username"])
        form = CreateUserForm(data=self.user_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_username_case_insensitivity(self):
        UserFactory(username="existinguser")
        self.user_data["username"] = "ExistingUser"
        form = CreateUserForm(data=self.user_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_save_creates_user(self):
        form = CreateUserForm(data=self.user_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, self.user_data["username"])
        self.assertEqual(user.email, self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password1"]))


class UpdateUserFormTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="updateuser", email="updateuser@example.com")

    def test_instantiation(self):
        form = UpdateUserForm(data={"public_name": "The Boss"}, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_update(self):
        form = UpdateUserForm(
            data={
                "public_name": "New Name",
                "about": "New About",
                "is_public": False,
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.public_name, "New Name")
        self.assertEqual(self.user.about, "New About")
        self.assertFalse(self.user.is_public)

    def test_public_name_validation(self):
        from django.conf import settings

        invalid_name = settings.SITE_NAME

        # Test exact match
        form = UpdateUserForm(
            data={"public_name": invalid_name},
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("public_name", form.errors)

        # Test case insensitive
        form = UpdateUserForm(
            data={"public_name": invalid_name.lower()},
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("public_name", form.errors)

        # Test with spaces
        spaced_name = " ".join(list(invalid_name))
        form = UpdateUserForm(
            data={"public_name": spaced_name},
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("public_name", form.errors)

    def test_avatar_update(self):
        avatar = self.get_uploaded_file(name="avatar.png")
        data = {"public_name": "Avatar User"}
        files = {"avatar": avatar}
        form = UpdateUserForm(data=data, files=files, instance=self.user)  # type: ignore
        self.assertTrue(form.is_valid())
        form.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)
        self.assertTrue(self.user.avatar.name.startswith("avatars/"))
