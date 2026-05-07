from django import template

register = template.Library()


@register.simple_tag
def file_count(user) -> int:
    """Count files owned by user"""
    total_files = 0
    if user is not None and user.is_authenticated:
        total_files = user.files.count()
    return total_files
