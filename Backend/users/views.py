from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import Job, SavedJob, UserPreference
from jobs.serializers import JobSerializer, UserPreferenceSerializer

from .permissions import IsTelegramUser
from .telegram_auth import TelegramWebAppAuthentication


def _empty_preferences() -> dict:
    """Default preference structure returned before the user completes onboarding."""
    return {
        "job_types": [],
        "fields": [],
        "location_type": "cambodia",
        "country": None,
        "onboarding_completed": False,
    }


def _saved_ids_for(user) -> set[int]:
    return set(SavedJob.objects.filter(user=user).values_list("job_id", flat=True))


class ProfileView(APIView):
    """GET /api/profile/ — the authenticated user's profile and preferences.

    Returns the Telegram user's id together with their saved preferences (or
    empty defaults if they have not yet completed onboarding).
    """

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def get(self, request):
        try:
            prefs = UserPreferenceSerializer(request.user.preferences).data
        except UserPreference.DoesNotExist:
            prefs = _empty_preferences()
        return Response(
            {
                "telegram_id": request.user.telegram_id,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "username": request.user.username,
                "preferences": prefs,
            }
        )


class PreferencesView(APIView):
    """GET/PUT/POST /api/profile/preferences/ — read and save user preferences.

    GET  → returns the user's current preferences (or empty defaults).
    PUT  → upserts the user's preferences and marks onboarding as completed.
    POST → alias for PUT (used for first-time preference creation).
    """

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def get(self, request):
        try:
            prefs = UserPreferenceSerializer(request.user.preferences).data
        except UserPreference.DoesNotExist:
            prefs = _empty_preferences()
        return Response(prefs)

    def _upsert(self, request):
        instance = UserPreference.objects.filter(user=request.user).first()
        serializer = UserPreferenceSerializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, onboarding_completed=True)
        return Response(
            {
                "telegram_id": request.user.telegram_id,
                "preferences": serializer.data,
            }
        )

    def put(self, request):
        return self._upsert(request)

    def post(self, request):
        return self._upsert(request)


class SavedJobsView(APIView):
    """GET /api/profile/saved/ — the current user's saved jobs.

    Also accessible at GET /api/jobs/saved/ (kept for backwards compat).
    """

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def get(self, request):
        job_ids = list(
            SavedJob.objects.filter(user=request.user).values_list("job_id", flat=True)
        )
        jobs = Job.objects.filter(id__in=job_ids)
        saved_ids = _saved_ids_for(request.user)
        serializer = JobSerializer(jobs, many=True, context={"saved_ids": saved_ids})
        return Response({"results": serializer.data, "count": len(serializer.data)})
