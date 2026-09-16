from django.urls import path

from . import views

urlpatterns = [
    # GET /api/profile/           — profile + preferences
    path("", views.ProfileView.as_view(), name="profile"),
    # GET /api/profile/preferences/   — preferences only
    # PUT /api/profile/preferences/   — save/update preferences
    # POST /api/profile/preferences/  — alias for PUT (first-time save)
    path("preferences/", views.PreferencesView.as_view(), name="profile-preferences"),
    # GET /api/profile/saved/     — saved jobs (proxied here for cleaner profile URL)
    path("saved/", views.SavedJobsView.as_view(), name="profile-saved"),
]
