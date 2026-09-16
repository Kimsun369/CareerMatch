from django.db import models

from users.models import TelegramUser

# ── Choice constants ─────────────────────────────────────────────────────────
# These are static taxonomy definitions that mirror the CareerMatch onboarding
# UI options. They are NOT application records — they describe the fixed set
# of categories the user can select, corresponding as closely as possible to
# the ReliefWeb "type of job" / "career categories" taxonomies.

JOB_TYPE_CHOICES = [
    ("full_time", "Full-time job"),
    ("part_time", "Part-time / Flexible"),
    ("internship", "Internship"),
    ("freelance", "Freelance / Gig"),
]

FIELD_CHOICES = [
    ("hotel_tourism", "Hotel & Tourism"),
    ("tech_it", "Tech & IT"),
    ("marketing_sales", "Marketing & Sales"),
    ("health_ngo", "Health & NGO"),
    ("finance_banking", "Finance & Banking"),
    ("education_teaching", "Education & Teaching"),
    ("construction_engineering", "Construction & Engineering"),
    ("logistics_supply_chain", "Logistics & Supply Chain"),
    ("any", "Any / Show me everything"),
]

LOCATION_TYPE_CHOICES = [
    ("cambodia", "Cambodia"),
    ("abroad", "Abroad"),
]


class UserPreference(models.Model):
    """Persisted onboarding preferences for a single Telegram user.

    All values are stored in the database — never only in frontend state.
    Multi-select fields (job_types, fields) are stored as JSON lists of the
    codes defined in the choice constants above.
    """

    user = models.OneToOneField(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    job_types = models.JSONField(default=list, blank=True)
    fields = models.JSONField(default=list, blank=True)
    location_type = models.CharField(
        max_length=16,
        choices=LOCATION_TYPE_CHOICES,
        default="cambodia",
    )
    country = models.CharField(max_length=100, blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self) -> str:
        return f"Preferences for {self.user}"


class Job(models.Model):
    """A normalised job/vacancy record ingested from ReliefWeb.

    Populated exclusively by the ingestion pipeline (jobs.reliefweb).
    Never created by hand as sample/test data in production code.
    Never written to by the frontend.

    Fields:
        source          — always "reliefweb" for now; ready for more sources.
        source_id       — ReliefWeb's own report id (unique per source).
        title           — job title.
        organization    — hiring organisation name.
        location        — city/region (ReliefWeb often only provides country).
        country         — country name as given by ReliefWeb.
        job_type        — best-effort mapping to our taxonomy; null if unknown.
        field           — best-effort mapping to our taxonomy; null if unknown.
        description     — full job description body from ReliefWeb.
        skills          — structured skills list (empty for ReliefWeb).
        closing_date    — application deadline.
        published_date  — date the listing was published.
        source_name     — human-readable source label (e.g. "ReliefWeb").
        source_url      — canonical URL to apply / view the listing.
        raw_metadata    — original ReliefWeb payload for debugging/re-mapping.
        is_active       — False when the job is past its closing date or removed.
    """

    source = models.CharField(max_length=50, default="reliefweb")
    source_id = models.CharField(max_length=100)

    title = models.CharField(max_length=500)
    organization = models.CharField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    # Best-effort mapping from ReliefWeb taxonomy; null when the source does
    # not specify or we cannot determine the correct mapping.
    job_type = models.CharField(
        max_length=32, choices=JOB_TYPE_CHOICES, blank=True, null=True
    )
    field = models.CharField(
        max_length=32, choices=FIELD_CHOICES, blank=True, null=True
    )

    description = models.TextField(blank=True, default="")
    skills = models.JSONField(default=list, blank=True)

    closing_date = models.DateField(blank=True, null=True)
    published_date = models.DateField(blank=True, null=True)

    source_name = models.CharField(max_length=100, default="ReliefWeb")
    source_url = models.URLField(max_length=1000)

    # Keep the full raw payload so we can re-normalise without re-fetching.
    raw_metadata = models.JSONField(blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_id"], name="unique_source_job"
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "job_type"]),
            models.Index(fields=["is_active", "field"]),
            models.Index(fields=["is_active", "country"]),
        ]
        ordering = ["-published_date", "-created_at"]
        verbose_name = "Job"
        verbose_name_plural = "Jobs"

    def __str__(self) -> str:
        return f"{self.title} @ {self.organization or 'Unknown Org'}"


class SavedJob(models.Model):
    """A job bookmarked by a user.

    The unique constraint prevents a user from saving the same job twice;
    callers should use ``get_or_create`` rather than catching IntegrityError.
    """

    user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="saved_jobs"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job"], name="unique_saved_job"
            ),
        ]
        ordering = ["-created_at"]
        verbose_name = "Saved Job"
        verbose_name_plural = "Saved Jobs"

    def __str__(self) -> str:
        return f"{self.user} → {self.job_id}"
