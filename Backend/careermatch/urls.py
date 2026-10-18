"""URL configuration for the CareerMatch project."""

from django.contrib import admin
from django.urls import include, path

from .views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/jobs/", include("jobs.urls")),
    path("api/profile/", include("users.urls")),
]
