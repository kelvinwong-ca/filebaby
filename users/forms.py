import re

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("public_name", "about", "avatar", "is_public")
        widgets = {
            "public_name": forms.TextInput(attrs={"class": "form-control"}),
            "about": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_public_name(self):
        public_name = self.cleaned_data.get("public_name", "").strip()
        pattern = r"\b" + r"\s*".join(re.escape(c) for c in settings.SITE_NAME)
        if re.search(pattern, public_name, re.IGNORECASE):
            raise forms.ValidationError(
                f'Public name cannot contain the term: "{settings.SITE_NAME}".'
            )
        return public_name
