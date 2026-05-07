import uuid
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image

from common.cases import BaseTestCase
from users.tests import PASSWORD
from users.tests.factories import UserFactory

User = get_user_model()


class SignInViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("users:signin")

    def test_signin_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_signin_post(self):
        """Test that a user can log in with valid credentials."""
        response = self.client.post(
            self.url,
            {"username": self.member.username, "password": PASSWORD},
        )
        # Should redirect after successful signin
        # By default redirects to /accounts/profile/ if LOGIN_REDIRECT_URL not set
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))

        # Verify user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_signin_post_failure(self):
        """Test that signin fails with invalid credentials."""
        response = self.client.post(
            self.url,
            {"username": self.member.username, "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("__all__", form.errors)
        self.assertEqual(
            form.errors["__all__"],
            [
                "Please enter a correct username and password. Note that both fields may be case-sensitive."
            ],
        )

        # Verify user is not authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class LogoutViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("users:logout")

    def test_logout_post(self):
        # First, log in the user
        self.client.login(username=self.member.username, password=PASSWORD)
        assert self.member.is_authenticated

        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify user is logged out
        response = self.client.get(reverse("users:signin"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_get(self):
        """Test that GET request to logout view is not allowed (405)."""
        self.mute()
        response = self.client.get(self.url)
        self.unmute()
        self.assertEqual(response.status_code, 405)


class SignUpViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("users:signup")

    def test_signup_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/signup.html")

    def test_signup_post(self):
        """Test that a new user can sign up."""
        username = "newuser"
        email = "newuser@example.com"
        password = "StrongPassword123!"

        response = self.client.post(
            self.url,
            {
                "username": username,
                "email": email,
                "password1": password,
                "password2": password,
            },
        )

        # Should redirect to signin page
        self.assertRedirects(response, reverse("users:signin"))

        # Verify user was created
        self.assertTrue(User.objects.filter(username=username).exists())
        user: Any = User.objects.get(username=username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_signup_post_invalid(self):
        """Test that signup fails with password mismatch."""
        username = "newuser"
        email = "newuser@example.com"
        password = "StrongPassword123!"

        response = self.client.post(
            self.url,
            {
                "username": username,
                "email": email,
                "password1": password,
                "password2": "mismatch",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/signup.html")
        form = response.context["form"]
        self.assertTrue(form.errors)

        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username=username).exists())


class PasswordChangeViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("users:password_change")

    def test_password_change_get(self):
        """Test that the password change form loads for authenticated users."""
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_change_form.html")

    def test_password_change_protected(self):
        """Test that unauthenticated users cannot access password change."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")

    def test_password_change_post_success(self):
        """Test that the password can be changed successfully."""
        self.client.force_login(self.member)
        new_password = "NewStrongPassword456!"

        # Note: PasswordChangeForm requires the OLD password
        response = self.client.post(
            self.url,
            {
                "old_password": PASSWORD,
                "new_password1": new_password,
                "new_password2": new_password,
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("users:password_change_done"))
        self.assertTemplateUsed(response, "users/password_change_done.html")

        # Verify password changed
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(new_password))

    def test_password_change_post_invalid(self):
        """Test that password change fails with invalid data."""
        self.client.force_login(self.member)

        response = self.client.post(
            self.url,
            {
                "old_password": "wrongpassword",
                "new_password1": "NewPass",
                "new_password2": "NewPass",
            },
        )

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)


class PasswordResetViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_password_reset_get(self):
        response = self.client.get(reverse("users:password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset_form.html")

    def test_password_reset_post(self):
        """Test that a password reset email is sent."""
        email = self.member.email
        response = self.client.post(reverse("users:password_reset"), {"email": email})

        self.assertRedirects(response, reverse("users:password_reset_done"))

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(email, mail.outbox[0].to)

    def test_password_reset_done_get(self):
        response = self.client.get(reverse("users:password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset_done.html")

    def test_password_reset_confirm(self):
        """Test the password reset confirmation view (link clicked from email)."""
        # Generate token and uid
        uid = urlsafe_base64_encode(force_bytes(self.member.pk))
        token = default_token_generator.make_token(self.member)

        url = reverse(
            "users:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
        )

        # Test GET (viewing the form)
        # Note: Django redirects to a 'set-password' URL to hide the token
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset_confirm.html")

        # The view redirects to a URL with token='set-password'
        confirm_url = reverse(
            "users:password_reset_confirm",
            kwargs={"uidb64": uid, "token": "set-password"},
        )

        # Test POST (changing the password)
        new_password = "NewStrongPassword123!"
        response = self.client.post(
            confirm_url,
            {
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )

        self.assertRedirects(response, reverse("users:password_reset_complete"))

        # Verify password changed
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(new_password))

    def test_password_reset_complete_get(self):
        response = self.client.get(reverse("users:password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset_complete.html")


class ProfileViewTestCase(BaseTestCase):
    """
    There are two ways to access ProfileView, via slug or without.
    Without a slug shows your own profile, whereas with a slug shows the public profile
    of another user.

    Profiles can also be private.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("users:profile")

    def test_profile_get(self):
        """Test the profile page loads for an authenticated user."""
        self.client.force_login(self.private)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_detail.html")
        self.assertEqual(response.context["object"], self.private)
        self.assertContains(response, self.private.username)
        self.assertContains(response, self.private.email)

    def test_profile_protected(self):
        """Test that unauthenticated users cannot access the profile view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")


class ProfileUpdateViewTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("users:update")

    def test_profile_update_get(self):
        """Test the profile update form loads for an authenticated user."""
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_form.html")
        self.assertEqual(response.context["object"], self.member)

    def test_profile_update_post(self):
        """Test that the profile can be updated."""
        self.client.force_login(self.member)
        data = {
            "public_name": "New Name",
            "about": "New About",
            "is_public": False,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("users:profile"))

        self.member.refresh_from_db()
        self.assertEqual(self.member.public_name, "New Name")
        self.assertEqual(self.member.about, "New About")
        self.assertFalse(self.member.is_public)

    def test_profile_update_post_cannot_contain_prohibited_term(self):
        """Test that the profile can be updated."""
        self.client.force_login(self.member)
        prohibit = settings.SITE_NAME
        data = {
            "public_name": f"321-{prohibit}",
            "about": "New About",
            "is_public": False,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("public_name", form.errors)
        self.assertIn(
            "Public name cannot contain the term", form.errors["public_name"][0]
        )

    def test_profile_update_avatar(self):
        """Test that the avatar can be updated."""
        self.client.force_login(self.member)
        guid = str(uuid.uuid4())
        expected_fname = f"{guid}.png"
        image = self.create_image(200, 200)  # Too big, will be resized
        test_file = self.get_uploaded_file(name=expected_fname, image=image)
        data = {
            "avatar": test_file,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("users:profile"))

        self.member.refresh_from_db()
        self.assertIsNotNone(self.member.avatar)
        self.assertTrue(self.member.avatar.name.endswith(expected_fname))

        pil_image = Image.open(self.member.avatar)
        self.assertEqual(pil_image.size, (150, 150))  # Confirm resized

    def test_profile_update_protected(self):
        """Test that unauthenticated users cannot access the update view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")
