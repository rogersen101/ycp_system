from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import dashboard


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "",
        dashboard,
        name="dashboard",
    ),

    path(
        "accounts/",
        include("accounts.urls"),
    ),

    path(
        "learning/",
        include("learning.urls"),
    ),
    path(
    "assessments/",
    include("assessments.urls"),
),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )