"""
URL configuration for filebaby project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("files/", include("files.urls")),
    path("users/", include("users.urls")),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico"),
    ),
    path(
        "site.webmanifest",
        RedirectView.as_view(url=settings.STATIC_URL + "site.webmanifest"),
    ),
    path(
        "android-chrome-192x192.png",
        RedirectView.as_view(url=settings.STATIC_URL + "android-chrome-192x192.png"),
    ),
    path(
        "android-chrome-512x512.png",
        RedirectView.as_view(url=settings.STATIC_URL + "android-chrome-512x512.png"),
    ),
    path(
        "apple-touch-icon.png",
        RedirectView.as_view(url=settings.STATIC_URL + "apple-touch-icon.png"),
    ),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
