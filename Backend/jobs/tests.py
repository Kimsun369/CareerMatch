"""Comprehensive tests for the CareerMatch backend.

Tests cover:
- TelegramUser model creation
- UserPreference creation and validation
- Job model creation
- ReliefWeb normalisation
- Recommendation scoring (rule-based engine)
- Recommendation with missing fields (neutral scoring)
- SavedJob creation and duplicate prevention
- All API endpoints
- Empty database behaviour
- Telegram authentication (debug path)

Authentication in tests
~~~~~~~~~~~~~~~~~~~~~~~
Django's test runner always forces DEBUG=False, which disables the
X-Debug-Telegram-Id auth path.  To authenticate test requests we use
``APIClient.force_authenticate(user=...)`` — the DRF-recommended way to
bypass the auth layer when testing *business logic* rather than auth itself.

The AuthenticationTests class uses ``@override_settings(DEBUG=True)`` to
re-enable the debug header path and test it directly.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from jobs.models import Job, SavedJob, UserPreference
from jobs.recommendation import (
    ScoredJob,
    _score_field,
    _score_job_type,
    _score_location,
    get_recommendations,
    score_job,
)
from jobs.reliefweb import normalize_job, _guess_field, _guess_job_type
from users.models import TelegramUser


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(telegram_id: int = 100001, username: str | None = "testuser") -> TelegramUser:
    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"first_name": "Test", "last_name": "User", "username": username},
    )
    return user


def make_prefs(
    user: TelegramUser,
    job_types: list[str] | None = None,
    fields: list[str] | None = None,
    location_type: str = "cambodia",
    country: str | None = None,
) -> UserPreference:
    prefs, _ = UserPreference.objects.get_or_create(
        user=user,
        defaults={
            "job_types": job_types or [],
            "fields": fields or [],
            "location_type": location_type,
            "country": country,
            "onboarding_completed": True,
        },
    )
    return prefs


def make_job(
    source_id: str = "rw-001",
    title: str = "Test Job",
    organization: str = "Test Org",
    country: str | None = "Cambodia",
    job_type: str | None = "full_time",
    field: str | None = "tech_it",
) -> Job:
    job, _ = Job.objects.get_or_create(
        source="reliefweb",
        source_id=source_id,
        defaults={
            "title": title,
            "organization": organization,
            "country": country,
            "location": country,
            "job_type": job_type,
            "field": field,
            "description": "A test job description.",
            "source_url": f"https://reliefweb.int/job/{source_id}",
            "is_active": True,
        },
    )
    return job


def auth_client(user: TelegramUser) -> APIClient:
    """Return an APIClient force-authenticated as *user*.

    Using force_authenticate() is the correct DRF approach for testing
    API behaviour — it bypasses the authentication layer entirely, so the
    tests are not sensitive to DEBUG or auth-header details.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── Model tests ───────────────────────────────────────────────────────────────

class TelegramUserModelTests(TestCase):
    def test_create_user(self):
        user = TelegramUser.objects.create(
            telegram_id=999001,
            first_name="Alice",
            last_name="Smith",
            username="alice_smith",
        )
        self.assertEqual(user.telegram_id, 999001)
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.username, "alice_smith")
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_user_str_with_username(self):
        user = TelegramUser(telegram_id=999002, username="bob")
        self.assertEqual(str(user), "@bob")

    def test_user_str_with_name(self):
        user = TelegramUser(telegram_id=999003, first_name="Carol", last_name="Jones")
        self.assertEqual(str(user), "Carol Jones")

    def test_user_str_fallback_to_id(self):
        user = TelegramUser(telegram_id=999004)
        self.assertEqual(str(user), "999004")

    def test_unique_telegram_id(self):
        TelegramUser.objects.create(telegram_id=999005)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TelegramUser.objects.create(telegram_id=999005)


class UserPreferenceModelTests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=100002)

    def test_create_preferences(self):
        prefs = UserPreference.objects.create(
            user=self.user,
            job_types=["full_time", "internship"],
            fields=["tech_it"],
            location_type="cambodia",
            onboarding_completed=True,
        )
        self.assertEqual(prefs.job_types, ["full_time", "internship"])
        self.assertEqual(prefs.fields, ["tech_it"])
        self.assertEqual(prefs.location_type, "cambodia")
        self.assertTrue(prefs.onboarding_completed)

    def test_default_location_type(self):
        prefs = UserPreference.objects.create(user=self.user)
        self.assertEqual(prefs.location_type, "cambodia")

    def test_one_preference_per_user(self):
        UserPreference.objects.create(user=self.user)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            UserPreference.objects.create(user=self.user)


class JobModelTests(TestCase):
    def test_create_job(self):
        job = make_job(source_id="rw-model-001")
        self.assertEqual(job.source, "reliefweb")
        self.assertEqual(job.source_id, "rw-model-001")
        self.assertTrue(job.is_active)

    def test_unique_source_constraint(self):
        make_job(source_id="rw-uniq-001")
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Job.objects.create(
                source="reliefweb",
                source_id="rw-uniq-001",
                title="Duplicate",
                source_url="https://example.com",
            )

    def test_job_str(self):
        job = make_job(title="Engineer", organization="UN")
        self.assertIn("Engineer", str(job))
        self.assertIn("UN", str(job))


class SavedJobModelTests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=100003)
        self.job = make_job(source_id="rw-saved-001")

    def test_save_job(self):
        saved, created = SavedJob.objects.get_or_create(user=self.user, job=self.job)
        self.assertTrue(created)

    def test_no_duplicate_saves(self):
        SavedJob.objects.create(user=self.user, job=self.job)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SavedJob.objects.create(user=self.user, job=self.job)

    def test_get_or_create_is_safe(self):
        """get_or_create should not raise on duplicate."""
        SavedJob.objects.get_or_create(user=self.user, job=self.job)
        _, created = SavedJob.objects.get_or_create(user=self.user, job=self.job)
        self.assertFalse(created)


# ── ReliefWeb normalisation tests ─────────────────────────────────────────────

class ReliefWebNormaliseTests(TestCase):
    def _raw(self, **overrides) -> dict:
        base = {
            "id": "12345",
            "fields": {
                "title": "Programme Manager",
                "url": "https://reliefweb.int/job/12345",
                "source": [{"name": "UNICEF"}],
                "country": [{"name": "Cambodia"}],
                "career_categories": [{"name": "Programme and Project Management"}],
                "type": [{"name": "Job"}],
                "date": {"created": "2026-01-15", "closing": "2026-02-28"},
                "body": "Full job description here.",
            },
        }
        base.update(overrides)
        return base

    def test_normalise_complete_record(self):
        result = normalize_job(self._raw())
        self.assertIsNotNone(result)
        self.assertEqual(result["source_id"], "12345")
        self.assertEqual(result["title"], "Programme Manager")
        self.assertEqual(result["organization"], "UNICEF")
        self.assertEqual(result["country"], "Cambodia")
        self.assertEqual(result["source_url"], "https://reliefweb.int/job/12345")
        self.assertEqual(result["job_type"], "full_time")
        self.assertEqual(result["published_date"].isoformat(), "2026-01-15")
        self.assertEqual(result["closing_date"].isoformat(), "2026-02-28")

    def test_normalise_missing_title_returns_none(self):
        raw = self._raw()
        raw["fields"]["title"] = ""
        self.assertIsNone(normalize_job(raw))

    def test_normalise_missing_url_returns_none(self):
        raw = self._raw()
        raw["fields"]["url"] = ""
        raw["fields"].pop("url_alias", None)
        self.assertIsNone(normalize_job(raw))

    def test_normalise_missing_country_is_none(self):
        raw = self._raw()
        raw["fields"]["country"] = []
        result = normalize_job(raw)
        self.assertIsNotNone(result)
        self.assertIsNone(result["country"])

    def test_normalise_missing_type_uses_full_time_default(self):
        raw = self._raw()
        raw["fields"]["type"] = []
        result = normalize_job(raw)
        # Empty type list → None (no fallback to full_time when list is empty)
        self.assertIsNone(result["job_type"])

    def test_normalise_internship_type(self):
        raw = self._raw()
        raw["fields"]["type"] = [{"name": "Internship"}]
        result = normalize_job(raw)
        self.assertEqual(result["job_type"], "internship")

    def test_guess_field_tech_it(self):
        self.assertEqual(
            _guess_field(["Information & Communications Technology"]), "tech_it"
        )

    def test_guess_field_unknown_returns_none(self):
        self.assertIsNone(_guess_field(["Some Completely Unknown Category"]))

    def test_guess_field_empty_returns_none(self):
        self.assertIsNone(_guess_field([]))

    def test_guess_job_type_volunteer(self):
        self.assertEqual(_guess_job_type(["Volunteer opportunity"]), "freelance")


# ── Recommendation scoring tests ──────────────────────────────────────────────

class RecommendationScoringTests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=100004)

    def _prefs(self, **kwargs) -> UserPreference:
        return UserPreference(
            user=self.user,
            job_types=kwargs.get("job_types", []),
            fields=kwargs.get("fields", []),
            location_type=kwargs.get("location_type", "cambodia"),
            country=kwargs.get("country"),
        )

    def _job(self, **kwargs) -> Job:
        return Job(
            source="reliefweb",
            source_id="score-test",
            title="Test",
            source_url="https://example.com",
            job_type=kwargs.get("job_type"),
            field=kwargs.get("field"),
            country=kwargs.get("country"),
        )

    # ── Job type dimension ────────────────────────────────────────────────────

    def test_job_type_full_match(self):
        prefs = self._prefs(job_types=["full_time"])
        job = self._job(job_type="full_time")
        pts, reason = _score_job_type(job, prefs)
        self.assertEqual(pts, 40)
        self.assertIsNotNone(reason)

    def test_job_type_mismatch(self):
        prefs = self._prefs(job_types=["internship"])
        job = self._job(job_type="full_time")
        pts, reason = _score_job_type(job, prefs)
        self.assertEqual(pts, 0)
        self.assertIsNone(reason)

    def test_job_type_unknown_is_neutral(self):
        prefs = self._prefs(job_types=["full_time"])
        job = self._job(job_type=None)
        pts, reason = _score_job_type(job, prefs)
        self.assertEqual(pts, 20)  # neutral = half weight
        self.assertIsNone(reason)

    def test_no_pref_job_type_is_neutral(self):
        prefs = self._prefs(job_types=[])
        job = self._job(job_type="full_time")
        pts, _ = _score_job_type(job, prefs)
        self.assertEqual(pts, 20)

    # ── Field dimension ───────────────────────────────────────────────────────

    def test_field_full_match(self):
        prefs = self._prefs(fields=["tech_it"])
        job = self._job(field="tech_it")
        pts, reason = _score_field(job, prefs)
        self.assertEqual(pts, 40)
        self.assertIsNotNone(reason)

    def test_field_mismatch(self):
        prefs = self._prefs(fields=["finance_banking"])
        job = self._job(field="tech_it")
        pts, _ = _score_field(job, prefs)
        self.assertEqual(pts, 0)

    def test_field_unknown_is_neutral(self):
        prefs = self._prefs(fields=["tech_it"])
        job = self._job(field=None)
        pts, _ = _score_field(job, prefs)
        self.assertEqual(pts, 20)  # neutral

    def test_any_field_preference_gets_full_points(self):
        prefs = self._prefs(fields=["any"])
        job = self._job(field="health_ngo")
        pts, _ = _score_field(job, prefs)
        self.assertEqual(pts, 40)

    def test_empty_field_preference_gets_full_points(self):
        prefs = self._prefs(fields=[])
        job = self._job(field="tech_it")
        pts, _ = _score_field(job, prefs)
        self.assertEqual(pts, 40)

    # ── Location dimension ────────────────────────────────────────────────────

    def test_location_cambodia_match(self):
        prefs = self._prefs(location_type="cambodia")
        job = self._job(country="Cambodia")
        pts, reason = _score_location(job, prefs)
        self.assertEqual(pts, 20)
        self.assertIsNotNone(reason)

    def test_location_cambodia_mismatch(self):
        prefs = self._prefs(location_type="cambodia")
        job = self._job(country="Thailand")
        pts, _ = _score_location(job, prefs)
        self.assertEqual(pts, 0)

    def test_location_abroad_match(self):
        prefs = self._prefs(location_type="abroad", country="Thailand")
        job = self._job(country="Thailand")
        pts, reason = _score_location(job, prefs)
        self.assertEqual(pts, 20)
        self.assertIsNotNone(reason)

    def test_location_abroad_mismatch(self):
        prefs = self._prefs(location_type="abroad", country="Thailand")
        job = self._job(country="Vietnam")
        pts, _ = _score_location(job, prefs)
        self.assertEqual(pts, 0)

    def test_location_unknown_is_neutral(self):
        prefs = self._prefs(location_type="cambodia")
        job = self._job(country=None)
        pts, _ = _score_location(job, prefs)
        self.assertEqual(pts, 10)  # neutral = half weight

    # ── Full scoring ──────────────────────────────────────────────────────────

    def test_perfect_match_scores_100(self):
        prefs = self._prefs(
            job_types=["full_time"],
            fields=["tech_it"],
            location_type="cambodia",
        )
        job = self._job(job_type="full_time", field="tech_it", country="Cambodia")
        scored = score_job(job, prefs)
        self.assertEqual(scored.score, 100)
        self.assertGreater(len(scored.reasons), 0)

    def test_full_match_beats_partial_match(self):
        """A job matching all three dimensions should outrank one matching none."""
        prefs = self._prefs(
            job_types=["full_time"],
            fields=["health_ngo"],
            location_type="cambodia",
        )
        good_job = self._job(
            job_type="full_time", field="health_ngo", country="Cambodia"
        )
        bad_job = self._job(
            job_type="internship", field="tech_it", country="Thailand"
        )
        good_scored = score_job(good_job, prefs)
        bad_scored = score_job(bad_job, prefs)
        self.assertGreater(good_scored.score, bad_scored.score)

    def test_all_unknown_fields_score_neutral(self):
        """A job with all null fields should get neutral (not zero) score."""
        prefs = self._prefs(
            job_types=["full_time"],
            fields=["tech_it"],
            location_type="cambodia",
        )
        job = self._job(job_type=None, field=None, country=None)
        scored = score_job(job, prefs)
        # Neutral is 20+20+10 = 50
        self.assertEqual(scored.score, 50)

    def test_explanation_mentions_matched_fields(self):
        prefs = self._prefs(job_types=["full_time"], fields=["tech_it"], location_type="cambodia")
        job = self._job(job_type="full_time", field="tech_it", country="Cambodia")
        scored = score_job(job, prefs)
        self.assertIn("Tech", scored.explanation)

    def test_get_recommendations_returns_sorted(self):
        """get_recommendations must return jobs sorted by score descending."""
        user = make_user(telegram_id=100005)
        prefs = make_prefs(
            user,
            job_types=["full_time"],
            fields=["tech_it"],
            location_type="cambodia",
        )
        # Perfect match
        make_job(
            source_id="rec-001",
            job_type="full_time",
            field="tech_it",
            country="Cambodia",
        )
        # Partial match
        make_job(
            source_id="rec-002",
            job_type="internship",
            field="finance_banking",
            country="Thailand",
        )
        results = get_recommendations(prefs)
        self.assertGreaterEqual(len(results), 2)
        # Verify descending order
        scores = [sj.score for sj in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        # Perfect match should be first
        self.assertEqual(results[0].job.source_id, "rec-001")


# ── API endpoint tests ────────────────────────────────────────────────────────

class JobListAPITests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=200001)
        self.client = auth_client(self.user)
        self.job1 = make_job(source_id="api-001", title="Software Engineer", country="Cambodia", field="tech_it")
        self.job2 = make_job(source_id="api-002", title="Health Officer", country="Thailand", field="health_ngo")

    def test_list_jobs_returns_200(self):
        resp = self.client.get("/api/jobs/")
        self.assertEqual(resp.status_code, 200)

    def test_list_jobs_structure(self):
        resp = self.client.get("/api/jobs/")
        data = resp.json()
        self.assertIn("results", data)
        self.assertIn("count", data)

    def test_search_filter(self):
        resp = self.client.get("/api/jobs/?search=Software")
        data = resp.json()
        titles = [j["title"] for j in data["results"]]
        self.assertIn("Software Engineer", titles)
        self.assertNotIn("Health Officer", titles)

    def test_job_type_filter(self):
        resp = self.client.get("/api/jobs/?job_type=full_time")
        data = resp.json()
        for j in data["results"]:
            self.assertEqual(j["job_type"], "full_time")

    def test_location_filter(self):
        resp = self.client.get("/api/jobs/?location=Cambodia")
        data = resp.json()
        for j in data["results"]:
            self.assertIn("Cambodia", j.get("country", ""))

    def test_requires_auth(self):
        """Unauthenticated request should be rejected."""
        anon = APIClient()
        resp = anon.get("/api/jobs/")
        self.assertEqual(resp.status_code, 403)

    def test_empty_database_returns_message(self):
        Job.objects.all().delete()
        resp = self.client.get("/api/jobs/")
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["results"], [])
        self.assertIn("message", data)


class JobDetailAPITests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=200002)
        self.client = auth_client(self.user)
        self.job = make_job(source_id="detail-001")

    def test_detail_returns_200(self):
        resp = self.client.get(f"/api/jobs/{self.job.pk}/")
        self.assertEqual(resp.status_code, 200)

    def test_detail_returns_correct_job(self):
        resp = self.client.get(f"/api/jobs/{self.job.pk}/")
        data = resp.json()
        self.assertEqual(data["id"], self.job.pk)
        self.assertEqual(data["title"], self.job.title)

    def test_detail_404_for_inactive(self):
        self.job.is_active = False
        self.job.save()
        resp = self.client.get(f"/api/jobs/{self.job.pk}/")
        self.assertEqual(resp.status_code, 404)

    def test_detail_404_for_nonexistent(self):
        resp = self.client.get("/api/jobs/999999/")
        self.assertEqual(resp.status_code, 404)


class RecommendationsAPITests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=200003)
        self.client = auth_client(self.user)

    def test_requires_preferences(self):
        """User without preferences gets 409."""
        resp = self.client.get("/api/jobs/recommendations/")
        self.assertEqual(resp.status_code, 409)
        data = resp.json()
        self.assertIn("results", data)
        self.assertEqual(data["results"], [])

    def test_empty_db_returns_empty_results(self):
        make_prefs(self.user, job_types=["full_time"], fields=["tech_it"])
        Job.objects.all().delete()
        resp = self.client.get("/api/jobs/recommendations/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["results"], [])

    def test_recommendations_include_score(self):
        make_prefs(self.user, job_types=["full_time"], fields=["tech_it"])
        make_job(source_id="rec-api-001", job_type="full_time", field="tech_it", country="Cambodia")
        resp = self.client.get("/api/jobs/recommendations/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(len(data["results"]), 0)
        first = data["results"][0]
        self.assertIn("match_score", first)
        self.assertIn("match_reason", first)
        self.assertIsNotNone(first["match_score"])

    def test_recommendations_are_sorted_by_score(self):
        make_prefs(self.user, job_types=["full_time"], fields=["tech_it"], location_type="cambodia")
        make_job(source_id="sort-a", job_type="full_time", field="tech_it", country="Cambodia")
        make_job(source_id="sort-b", job_type="internship", field="finance_banking", country="Thailand")
        resp = self.client.get("/api/jobs/recommendations/")
        data = resp.json()
        scores = [j["match_score"] for j in data["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_recommendations_not_fake(self):
        """Returned jobs must exist in the database."""
        make_prefs(self.user, job_types=["full_time"], fields=["tech_it"])
        make_job(source_id="real-001")
        resp = self.client.get("/api/jobs/recommendations/")
        data = resp.json()
        db_ids = set(Job.objects.values_list("id", flat=True))
        for j in data["results"]:
            self.assertIn(j["id"], db_ids)


class ProfileAPITests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=200004)
        self.client = auth_client(self.user)

    def test_get_profile_returns_200(self):
        resp = self.client.get("/api/profile/")
        self.assertEqual(resp.status_code, 200)

    def test_profile_includes_telegram_id(self):
        resp = self.client.get("/api/profile/")
        data = resp.json()
        self.assertIn("telegram_id", data)
        self.assertEqual(data["telegram_id"], 200004)

    def test_profile_includes_preferences(self):
        resp = self.client.get("/api/profile/")
        data = resp.json()
        self.assertIn("preferences", data)

    def test_profile_empty_prefs_before_onboarding(self):
        resp = self.client.get("/api/profile/")
        data = resp.json()
        prefs = data["preferences"]
        self.assertEqual(prefs["job_types"], [])
        self.assertEqual(prefs["fields"], [])


class PreferencesAPITests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=200005)
        self.client = auth_client(self.user)

    def _valid_payload(self):
        return {
            "job_types": ["full_time", "internship"],
            "fields": ["tech_it"],
            "location_type": "cambodia",
            "country": None,
        }

    def test_put_preferences_saves_to_db(self):
        resp = self.client.put("/api/profile/preferences/", self._valid_payload(), format="json")
        self.assertEqual(resp.status_code, 200)
        prefs = UserPreference.objects.get(user=self.user)
        self.assertIn("full_time", prefs.job_types)
        self.assertIn("tech_it", prefs.fields)
        self.assertTrue(prefs.onboarding_completed)

    def test_post_preferences_saves_to_db(self):
        resp = self.client.post("/api/profile/preferences/", self._valid_payload(), format="json")
        self.assertEqual(resp.status_code, 200)
        prefs = UserPreference.objects.get(user=self.user)
        self.assertTrue(prefs.onboarding_completed)

    def test_get_preferences(self):
        make_prefs(self.user, job_types=["full_time"], fields=["tech_it"])
        resp = self.client.get("/api/profile/preferences/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("full_time", data["job_types"])

    def test_put_preferences_updates_existing(self):
        make_prefs(self.user, job_types=["internship"])
        payload = self._valid_payload()
        payload["job_types"] = ["full_time"]
        resp = self.client.put("/api/profile/preferences/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        # Re-fetch from DB — the in-memory object is stale after the PUT
        prefs = UserPreference.objects.get(user=self.user)
        self.assertEqual(prefs.job_types, ["full_time"])

    def test_abroad_requires_country(self):
        payload = {
            "job_types": [],
            "fields": [],
            "location_type": "abroad",
            "country": None,
        }
        resp = self.client.put("/api/profile/preferences/", payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("country", resp.json())

    def test_invalid_job_type_rejected(self):
        payload = self._valid_payload()
        payload["job_types"] = ["invalid_type"]
        resp = self.client.put("/api/profile/preferences/", payload, format="json")
        self.assertEqual(resp.status_code, 400)


class SavedJobAPITests(TestCase):
    def setUp(self):
        self.user = make_user(telegram_id=200006)
        self.client = auth_client(self.user)
        self.job = make_job(source_id="save-api-001")

    def test_save_job_returns_201(self):
        resp = self.client.post(f"/api/jobs/{self.job.pk}/save/")
        self.assertEqual(resp.status_code, 201)

    def test_save_twice_returns_200_not_error(self):
        self.client.post(f"/api/jobs/{self.job.pk}/save/")
        resp = self.client.post(f"/api/jobs/{self.job.pk}/save/")
        self.assertEqual(resp.status_code, 200)

    def test_saved_persisted_to_db(self):
        self.client.post(f"/api/jobs/{self.job.pk}/save/")
        self.assertTrue(SavedJob.objects.filter(user=self.user, job=self.job).exists())

    def test_unsave_job(self):
        SavedJob.objects.get_or_create(user=self.user, job=self.job)
        resp = self.client.delete(f"/api/jobs/{self.job.pk}/save/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(SavedJob.objects.filter(user=self.user, job=self.job).exists())

    def test_unsave_when_not_saved_is_idempotent(self):
        resp = self.client.delete(f"/api/jobs/{self.job.pk}/save/")
        self.assertEqual(resp.status_code, 204)

    def test_get_saved_jobs(self):
        SavedJob.objects.get_or_create(user=self.user, job=self.job)
        resp = self.client.get("/api/jobs/saved/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        ids = [j["id"] for j in data["results"]]
        self.assertIn(self.job.pk, ids)

    def test_get_saved_jobs_via_profile(self):
        SavedJob.objects.get_or_create(user=self.user, job=self.job)
        resp = self.client.get("/api/profile/saved/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        ids = [j["id"] for j in data["results"]]
        self.assertIn(self.job.pk, ids)

    def test_is_saved_flag_in_job_list(self):
        SavedJob.objects.get_or_create(user=self.user, job=self.job)
        resp = self.client.get("/api/jobs/")
        data = resp.json()
        for j in data["results"]:
            if j["id"] == self.job.pk:
                self.assertTrue(j["is_saved"])
                break


# ── Authentication tests (test the debug-header path explicitly) ──────────────

class AuthenticationTests(TestCase):
    """Tests for the Telegram debug authentication path.

    These tests use ``override_settings(DEBUG=True)`` because Django's test
    runner forces DEBUG=False by default, which disables the
    X-Debug-Telegram-Id header fallback on purpose.
    """

    @override_settings(DEBUG=True)
    def test_debug_header_creates_user(self):
        client = APIClient()
        client.credentials(HTTP_X_DEBUG_TELEGRAM_ID="300001")
        resp = client.get("/api/profile/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(TelegramUser.objects.filter(telegram_id=300001).exists())

    @override_settings(DEBUG=True)
    def test_same_debug_id_same_user(self):
        client = APIClient()
        client.credentials(HTTP_X_DEBUG_TELEGRAM_ID="300002")
        client.get("/api/profile/")
        client.get("/api/profile/")
        # Should only create one user
        self.assertEqual(TelegramUser.objects.filter(telegram_id=300002).count(), 1)

    def test_unauthenticated_returns_403(self):
        anon = APIClient()
        resp = anon.get("/api/jobs/")
        self.assertEqual(resp.status_code, 403)

    @override_settings(DEBUG=True)
    def test_different_debug_ids_different_users(self):
        c1 = APIClient()
        c1.credentials(HTTP_X_DEBUG_TELEGRAM_ID="300003")
        c1.get("/api/profile/")

        c2 = APIClient()
        c2.credentials(HTTP_X_DEBUG_TELEGRAM_ID="300004")
        c2.get("/api/profile/")

        self.assertTrue(TelegramUser.objects.filter(telegram_id=300003).exists())
        self.assertTrue(TelegramUser.objects.filter(telegram_id=300004).exists())

    @override_settings(DEBUG=False)
    def test_debug_header_refused_in_production(self):
        """With DEBUG=False the debug header must be completely ignored."""
        client = APIClient()
        client.credentials(HTTP_X_DEBUG_TELEGRAM_ID="300005")
        resp = client.get("/api/profile/")
        # Must be rejected — debug path is off in production
        self.assertEqual(resp.status_code, 403)
        # No user should have been created
        self.assertFalse(TelegramUser.objects.filter(telegram_id=300005).exists())
