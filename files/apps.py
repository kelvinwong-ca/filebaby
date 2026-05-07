import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)
_magic_checked = False


class FilesConfig(AppConfig):
    name = "files"

    def ready(self):
        global _magic_checked

        import files.signals

        if not _magic_checked:
            _magic_checked = True

            try:
                import magic  # noqa: F401
            except ImportError as exc:
                error_text = str(exc)
                if "failed to find libmagic" in error_text.lower():
                    logger.warning(
                        "python-magic is installed but libmagic is missing. "
                        "Install libmagic on your system (macOS: 'brew install libmagic'; "
                        "Debian/Ubuntu: 'sudo apt-get install libmagic1'; "
                        "Fedora: 'sudo dnf install file-libs'). Original error: %s",
                        error_text,
                    )
                else:
                    raise exc
