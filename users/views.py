import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import CreateUserForm, UpdateUserForm
from .utils import resize_uploaded_image

logger = logging.getLogger(__name__)
User = get_user_model()


class SigninView(SuccessMessageMixin, LoginView):
    success_message = "Successfully signed in."


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = CreateUserForm
    success_url = reverse_lazy("users:signin")
    template_name = "users/signup.html"
    success_message = "Account created successfully. You can now sign in."


class ProfileView(DetailView):
    """Your own profile"""

    model = User

    def get_object(self, queryset=None):
        return self.request.user


class ProfileUpdateView(SuccessMessageMixin, UpdateView):
    model = User
    form_class = UpdateUserForm
    success_url = reverse_lazy("users:profile")
    success_message = "Profile updated successfully."

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form: Any):
        """
        Resize the profile image before saving
        """
        # image at this point is an django.core.files.uploadedfile.InMemoryUploadedFile
        image = form.cleaned_data.get("avatar")
        if image:
            form.instance.avatar = resize_uploaded_image(image)

        return super().form_valid(form)
