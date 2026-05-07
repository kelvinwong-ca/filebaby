from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import User


class FilebabyUserAdmin(UserAdmin):
    list_display = (
        "username",
        "is_active",
        "is_staff",
        "email",
        "public_name",
        "has_avatar",
        "is_public",
        "user_files_link",
    )
    search_fields = list(UserAdmin.search_fields) + ["public_name"]
    list_filter = list(UserAdmin.list_filter) + ["is_public"]
    actions = ["make_private", "activate_users", "deactivate_users"]
    readonly_fields = ["slug", "avatar_preview"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "email",
                    "public_name",
                    "about",
                    "avatar_preview",
                    "avatar",
                    "is_public",
                    "slug",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    @admin.action(description="Set selected users as private")
    def make_private(self, request, queryset):
        updated_count = queryset.update(is_public=False)
        self.message_user(
            request, f"{updated_count} users were successfully set to private."
        )

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        updated_count = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated_count} users were successfully activated."
        )

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        updated_count = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated_count} users were successfully deactivated."
        )

    @admin.display(boolean=True, description="Avatar")
    def has_avatar(self, obj):
        return bool(obj.avatar)

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.avatar.url,
            )
        return ""

    avatar_preview.short_description = "Avatar Preview"

    def user_files_link(self, obj):
        from files.models import File

        num_files = File.objects.by_owner(obj).count()
        url = reverse("admin:files_file_changelist") + f"?owner__id__exact={obj.id}"
        return format_html('<a href="{}">View Files ({})</a>', url, num_files)

    user_files_link.short_description = "User Files"


admin.site.register(User, FilebabyUserAdmin)
