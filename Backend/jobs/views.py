from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsTelegramUser
from users.telegram_auth import TelegramWebAppAuthentication

from .models import Job, SavedJob, UserPreference
from .recommendation import get_recommendations
from .serializers import JobSerializer


class JobPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _saved_ids_for(user) -> set[int]:
    """Return the set of Job PKs that this user has saved."""
    return set(SavedJob.objects.filter(user=user).values_list("job_id", flat=True))


class JobListView(APIView):
    """GET /api/jobs/ — paginated, filterable list of real job listings.

    Query parameters:
        search    — full-text search across title, organisation, description.
        job_type  — filter by job_type code (e.g. "full_time").
        field     — filter by field code (e.g. "tech_it").
        location  — filter by country name (case-insensitive contains).
        page      — page number (default 1).
        page_size — results per page (default 20, max 100).

    Returns an empty ``results`` list when no jobs match, NOT fake data.
    """

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def get(self, request):
        qs = Job.objects.filter(is_active=True)

        search = request.query_params.get("search", "").strip()
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(title__icontains=search)
                | Q(organization__icontains=search)
                | Q(description__icontains=search)
                | Q(country__icontains=search)
            )

        job_type = request.query_params.get("job_type", "").strip()
        if job_type:
            qs = qs.filter(job_type=job_type)

        field = request.query_params.get("field", "").strip()
        if field:
            qs = qs.filter(field=field)

        location = request.query_params.get("location", "").strip()
        if location:
            qs = qs.filter(country__icontains=location)

        if not qs.exists():
            return Response(
                {
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "results": [],
                    "message": "No jobs found. Run: python manage.py ingest_reliefweb",
                }
            )

        paginator = JobPagination()
        page = paginator.paginate_queryset(qs, request)
        saved_ids = _saved_ids_for(request.user)
        serializer = JobSerializer(page, many=True, context={"saved_ids": saved_ids})
        return paginator.get_paginated_response(serializer.data)


class JobDetailView(APIView):
    """GET /api/jobs/{id}/ — single job detail."""

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def get(self, request, pk: int):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        saved_ids = _saved_ids_for(request.user)
        serializer = JobSerializer(job, context={"saved_ids": saved_ids})
        return Response(serializer.data)


class RecommendationsView(APIView):
    """GET /api/jobs/recommendations/ — personalised, scored job recommendations.

    Identifies the current Telegram user, loads their preferences from
    PostgreSQL, scores all active jobs against those preferences using the
    rule-based engine, and returns the top matches ranked by score.

    Returns a 409 if the user has not yet completed onboarding (no saved
    preferences), so the frontend can redirect them to the onboarding flow.

    Returns an empty results list when no jobs exist in the database —
    never invents or hardcodes recommendations.
    """

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def get(self, request):
        try:
            prefs = request.user.preferences
        except UserPreference.DoesNotExist:
            return Response(
                {
                    "detail": "Complete onboarding before requesting recommendations.",
                    "results": [],
                    "count": 0,
                },
                status=status.HTTP_409_CONFLICT,
            )

        if not prefs.onboarding_completed:
            return Response(
                {
                    "detail": "Complete onboarding before requesting recommendations.",
                    "results": [],
                    "count": 0,
                },
                status=status.HTTP_409_CONFLICT,
            )

        scored = get_recommendations(prefs)

        if not scored:
            return Response(
                {
                    "results": [],
                    "count": 0,
                    "message": (
                        "No jobs available. "
                        "Run: python manage.py ingest_reliefweb"
                    ),
                }
            )

        saved_ids = _saved_ids_for(request.user)

        # Annotate each Job instance with its score and explanation so the
        # serialiser can expose them without a separate database query.
        for sj in scored:
            sj.job._match_score = sj.score
            sj.job._match_reason = sj.explanation
            sj.job._match_factors = sj.factors or []

        jobs = [sj.job for sj in scored]
        serializer = JobSerializer(jobs, many=True, context={"saved_ids": saved_ids})
        return Response({"results": serializer.data, "count": len(serializer.data)})


class SavedJobListView(APIView):
    """GET /api/jobs/saved/ — the current user's bookmarked jobs."""

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


class SaveJobView(APIView):
    """POST/DELETE /api/jobs/{id}/save/ — bookmark or unbookmark a job.

    POST   → save the job (idempotent: saving twice is not an error).
    DELETE → unsave the job (idempotent: unsaving when not saved is not an error).
    """

    authentication_classes = [TelegramWebAppAuthentication]
    permission_classes = [IsTelegramUser]

    def post(self, request, pk: int):
        job = get_object_or_404(Job, pk=pk)
        _, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if created:
            return Response(
                {"detail": "Job saved successfully."}, status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "Job was already saved."}, status=status.HTTP_200_OK
        )

    def delete(self, request, pk: int):
        SavedJob.objects.filter(user=request.user, job_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
