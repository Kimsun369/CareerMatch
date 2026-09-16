from django.urls import path

from . import views

# NOTE: order matters — more-specific paths must come before parameterised ones.
urlpatterns = [
    # GET  /api/jobs/recommendations/   — personalised scored recommendations
    path("recommendations/", views.RecommendationsView.as_view(), name="job-recommendations"),
    # GET  /api/jobs/saved/             — current user's bookmarked jobs
    path("saved/", views.SavedJobListView.as_view(), name="job-saved-list"),
    # POST /api/jobs/{id}/save/         — bookmark a job
    # DELETE /api/jobs/{id}/save/       — remove bookmark
    path("<int:pk>/save/", views.SaveJobView.as_view(), name="job-save"),
    # GET  /api/jobs/{id}/              — single job detail
    path("<int:pk>/", views.JobDetailView.as_view(), name="job-detail"),
    # GET  /api/jobs/                   — paginated job list
    path("", views.JobListView.as_view(), name="job-list"),
]
