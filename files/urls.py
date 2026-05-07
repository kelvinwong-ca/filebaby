from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import (
    FileCreateView,
    FileDeleteView,
    FileDetailView,
    FileDownloadView,
    FileListView,
)

app_name = "files"

urlpatterns = [
    path("", login_required(FileListView.as_view()), name="list"),
    path("from/<slug:slug>/", login_required(FileListView.as_view()), name="list_from"),
    path("<int:pk>/", login_required(FileDetailView.as_view()), name="detail"),
    path("create/", login_required(FileCreateView.as_view()), name="create"),
    path("delete/<int:pk>/", login_required(FileDeleteView.as_view()), name="delete"),
    path(
        "downloads/<int:pk>/",
        login_required(FileDownloadView.as_view()),
        name="download",
    ),
]
