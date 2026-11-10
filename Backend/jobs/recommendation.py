"""Rule-based recommendation engine.

Ranks active Job rows against a user's UserPreference using a transparent,
documented weighted score. No AI required — this is the reliable baseline the
rest of the app always falls back to.

Scoring (out of 100 points total):

Job type match  (40 pts)
    • 40 pts  — job.job_type is in the user's selected job_types.
    • 20 pts  — job.job_type is unknown/null (neutral: missing data ≠ mismatch).
    • 20 pts  — user selected no job types (no preference = all are fine).
    •  0 pts  — definite mismatch (both sides have a known type and they differ).

Field / sector match  (40 pts)
    • 40 pts  — job.field is in the user's selected fields, OR user chose "any".
    • 20 pts  — job.field is unknown/null (neutral).
    •  0 pts  — definite mismatch.

Location match  (20 pts)
    • 20 pts  — user wants Cambodia and job.country is Cambodia, OR user
                wants "abroad" and job.country matches their chosen country.
    • 10 pts  — job.country is unknown/null (neutral).
    •  0 pts  — definite mismatch.

Design principles:
    • Missing/unknown job fields are NEUTRAL, not disqualifying.
    • "unknown ≠ mismatch" — a job with no recorded type can still be surfaced.
    • All scoring is deterministic and transparent — no hidden weights.
"""

from __future__ import annotations

from dataclasses import dataclass

from jobs.models import FIELD_CHOICES, JOB_TYPE_CHOICES, Job, UserPreference

# ── Weights ───────────────────────────────────────────────────────────────────
JOB_TYPE_WEIGHT = 40
FIELD_WEIGHT = 40
LOCATION_WEIGHT = 20

_JOB_TYPE_LABELS: dict[str, str] = dict(JOB_TYPE_CHOICES)
_FIELD_LABELS: dict[str, str] = dict(FIELD_CHOICES)


@dataclass
class ScoredJob:
    job: Job
    score: int
    reasons: list[str]
    explanation_text: str | None = None
    factors: list[dict[str, str]] | None = None

    @property
    def explanation(self) -> str:
        if self.explanation_text:
            return self.explanation_text
        if not self.reasons:
            return "General match based on available job information."
        return " ".join(self.reasons)


# ── Individual dimension scorers ──────────────────────────────────────────────

def _score_job_type(job: Job, prefs: UserPreference) -> tuple[int, str | None]:
    """Score the job-type dimension.

    Returns (points, reason_string_or_None).
    """
    # User has no job-type preference → treat as neutral (they accept all types).
    if not prefs.job_types:
        return JOB_TYPE_WEIGHT // 2, None

    # Job has no recorded type → neutral (missing data, not a mismatch).
    if not job.job_type:
        return JOB_TYPE_WEIGHT // 2, None

    # Positive match.
    if job.job_type in prefs.job_types:
        label = _JOB_TYPE_LABELS.get(job.job_type, job.job_type)
        return JOB_TYPE_WEIGHT, f"Matches your interest in {label}."

    # Definite mismatch.
    return 0, None


def _score_field(job: Job, prefs: UserPreference) -> tuple[int, str | None]:
    """Score the field/sector dimension."""
    # "any" preference or empty list → user accepts all fields.
    if not prefs.fields or "any" in prefs.fields:
        return FIELD_WEIGHT, None

    # Job has no recorded field → neutral.
    if not job.field:
        return FIELD_WEIGHT // 2, None

    # Positive match.
    if job.field in prefs.fields:
        label = _FIELD_LABELS.get(job.field, job.field)
        return FIELD_WEIGHT, f"Matches your interest in {label}."

    # Definite mismatch.
    return 0, None


def _score_location(job: Job, prefs: UserPreference) -> tuple[int, str | None]:
    """Score the location dimension."""
    # Job has no recorded country → neutral.
    if not job.country:
        return LOCATION_WEIGHT // 2, None

    job_country = job.country.strip().lower()

    if prefs.location_type == "cambodia":
        if job_country == "cambodia":
            return LOCATION_WEIGHT, "Matches your preferred location (Cambodia)."
        return 0, None

    if prefs.location_type == "abroad" and prefs.country:
        if job_country == prefs.country.strip().lower():
            return LOCATION_WEIGHT, f"Matches your preferred location ({prefs.country})."
        return 0, None

    # No meaningful location preference set → neutral.
    return LOCATION_WEIGHT // 2, None


# ── Public API ────────────────────────────────────────────────────────────────

def score_job(job: Job, prefs: UserPreference) -> ScoredJob:
    """Score a single job against the user's preferences."""
    type_score, type_reason = _score_job_type(job, prefs)
    field_score, field_reason = _score_field(job, prefs)
    location_score, location_reason = _score_location(job, prefs)

    reasons = [r for r in (field_reason, type_reason, location_reason) if r]
    explanation_parts = list(reasons)
    factors: list[dict[str, str]] = []

    if prefs.fields and "any" not in prefs.fields:
        if not job.field:
            explanation_parts.append("The job field isn't listed, so we couldn't compare it with your interests.")
            factors.append({"category": "Field", "status": "unknown", "text": "Not listed"})
        elif job.field not in prefs.fields:
            selected_fields = ", ".join(_FIELD_LABELS.get(value, value) for value in prefs.fields)
            job_field = _FIELD_LABELS.get(job.field, job.field)
            explanation_parts.append(
                f"This role is in {job_field}, outside your selected fields ({selected_fields})."
            )
            factors.append({"category": "Field", "status": "different", "text": f"Different from {selected_fields}"})
        else:
            matched_fields = ", ".join(_FIELD_LABELS.get(value, value) for value in prefs.fields if value == job.field)
            factors.append({"category": "Field", "status": "match", "text": f"Matches {matched_fields}"})

    if prefs.job_types:
        if not job.job_type:
            explanation_parts.append("Job type details aren't available for this listing.")
            factors.append({"category": "Job type", "status": "unknown", "text": "Not listed"})
        elif job.job_type not in prefs.job_types:
            selected_types = ", ".join(_JOB_TYPE_LABELS.get(value, value) for value in prefs.job_types)
            job_type = _JOB_TYPE_LABELS.get(job.job_type, job.job_type)
            explanation_parts.append(
                f"This role's type ({job_type}) differs from your preference ({selected_types})."
            )
            factors.append({"category": "Job type", "status": "different", "text": f"Different from {selected_types}"})
        else:
            job_type = _JOB_TYPE_LABELS.get(job.job_type, job.job_type)
            factors.append({"category": "Job type", "status": "match", "text": f"Matches {job_type}"})

    if prefs.location_type in ("cambodia", "abroad"):
        preferred_location = "Cambodia" if prefs.location_type == "cambodia" else (prefs.country or "your selected country")
        if not job.country:
            explanation_parts.append(
                "Location details aren't available, so we couldn't check this against your preference."
            )
            factors.append({"category": "Location", "status": "unknown", "text": "Not listed"})
        else:
            matches_location = (
                job.country.strip().lower() == "cambodia"
                if prefs.location_type == "cambodia"
                else bool(prefs.country and job.country.strip().lower() == prefs.country.strip().lower())
            )
            if not matches_location:
                explanation_parts.append(
                    f"This role is listed in {job.country}, outside your preferred location ({preferred_location})."
                )
                factors.append({"category": "Location", "status": "different", "text": f"Outside {preferred_location}"})
            else:
                factors.append({"category": "Location", "status": "match", "text": f"Matches {preferred_location}"})

    if not explanation_parts:
        explanation_parts.append("Suggested based on your preferences and the job details available.")
    total = type_score + field_score + location_score
    return ScoredJob(
        job=job,
        score=total,
        reasons=reasons,
        explanation_text=" ".join(explanation_parts),
        factors=factors,
    )


def get_recommendations(prefs: UserPreference, limit: int = 30) -> list[ScoredJob]:
    """Return up to ``limit`` active jobs ranked by match score.

    All scoring is done in Python (not in SQL) to keep the algorithm portable
    and transparent. For larger datasets, consider caching or moving scoring
    to SQL expressions.
    """
    candidates = Job.objects.filter(is_active=True).select_related()
    scored = [score_job(job, prefs) for job in candidates]
    scored.sort(key=lambda sj: sj.score, reverse=True)
    return scored[:limit]
