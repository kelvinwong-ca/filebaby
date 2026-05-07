import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.db import DatabaseError
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView
from django_sendfile import sendfile

from .forms import FileForm
from .models import File

User = get_user_model()

logger = logging.getLogger(__name__)


class ModelOwnerMixin:
    """You can only see your own files."""

    request: Any
    model: Any

    def get_queryset(self):
        return self.model.objects.by_owner(self.request.user)


class FileCreateView(SuccessMessageMixin, CreateView):

    model = File
    form_class = FileForm
    success_url = reverse_lazy("files:list")
    success_message = "File uploaded successfully"
    upload_failed_message = "Upload failed. Please try again."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            return super().form_valid(form)
        except DatabaseError:
            logger.exception("File upload failed due to database error.")
            form.add_error("file", self.upload_failed_message)
            return self.form_invalid(form)

    def form_invalid(self, form: Any) -> HttpResponse:
        if (
            form.errors.get("file")
            and form.errors["file"][0] == "Unsupported file type."
        ):
            logger.warning("File upload failed with Unsupported file type error.")

        if self.request.headers.get("x-requested-by") == "Dropzone":
            file_errors = form.errors.get("file")
            error_message = (
                file_errors[0] if file_errors else self.upload_failed_message
            )
            return JsonResponse({"error": error_message}, status=400)

        return super().form_invalid(form)


class FileDetailView(DetailView):
    model = File
    request: Any

    def get_queryset(self):
        return self.model.objects.filter(
            Q(owner=self.request.user) | Q(owner__is_public=True)
        )


class FileListView(ListView):
    model: Any = File
    context_object_name = "files"
    paginate_by = 5
    slug_url_kwarg = "slug"
    slug_field = "slug"

    def get_queryset(self):
        self.files_from = None
        self.your_files = False
        if "slug" in self.kwargs:
            # Public users or private users viewing their own files
            user_filter = Q(is_public=True) | Q(pk=self.request.user.pk)
            try:
                user: Any = User.objects.get(user_filter, slug=self.kwargs["slug"])
            except User.DoesNotExist:
                logging.info(
                    "Accessible user with slug '%s' does not exist.",
                    self.kwargs["slug"],
                )
            else:
                self.files_from = user.best_name()
                if self.request.user == user:
                    self.files_from = "You"
                    self.your_files = True

                return self.model.objects.filter(owner=user)
            raise Http404
        publics = User.objects.filter(is_public=True)
        return self.model.objects.filter(owner__in=publics)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["files_from"] = self.files_from
        context["your_files"] = self.your_files
        return context


class FileDeleteView(ModelOwnerMixin, SuccessMessageMixin, DeleteView):
    model = File
    success_url = reverse_lazy("files:list")
    success_message = "File deleted successfully"


class FileDownloadView(DetailView):
    model = File
    request: Any

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return self.model.objects.all()

        return self.model.objects.filter(
            Q(owner=self.request.user) | Q(owner__is_public=True)
        )

    def render_to_response(self, context):
        """
        Serves the file as a download using django-sendfile.

        https://django-sendfile2.readthedocs.io/en/latest/index.html

        :param context: An unused dictionary
        """
        obj = self.get_object()
        path = obj.file.name
        content_type = obj.content_type
        return sendfile(
            self.request,
            filename=path,
            attachment=settings.FILEBABY_AS_ATTACHMENT,
            mimetype=content_type,
        )
