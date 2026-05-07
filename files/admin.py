from django.contrib import admin
from django.db.models import FileField
from django.forms import Widget
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.html import format_html

from .models import File


class FilenameWidget(Widget):
    """Renders the stored filename as plain text without a download link."""

    def render(self, name, value, attrs=None, renderer=None):
        if value:
            return format_html("<span>{}</span>", value)
        return "(no file)"


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ["filename_link", "owner_link", "content_type", "created", "updated"]
    list_filter = ["created", "updated", "content_type"]
    search_fields = ["filename", "owner__username", "owner__email"]
    readonly_fields = ["created", "updated"]
    formfield_overrides = {FileField: {"widget": FilenameWidget}}

    def filename_link(self, obj):
        url = reverse("admin:files_file_change", args=[obj.id])
        name = truncatechars(obj.filename, 50)
        return format_html('<a href="{}">{}</a>', url, name)

    filename_link.short_description = "Filename"
    filename_link.admin_order_field = "filename"

    def owner_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner)

    owner_link.short_description = "Owner"
    owner_link.admin_order_field = "owner"
