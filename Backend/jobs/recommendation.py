"""Rule-based recommendation engine.

Ranks active Job rows against a user's UserPreference using a transparent,
documented weighted score. No AI required — this is the reliable baseline the
rest of the app always falls back to.

Scoring (out of 100 points total):
───────────────────────────────────
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

    @property
    def explanation(self) -> str:
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
    total = type_score + field_score + location_score
    return ScoredJob(job=job, score=total, reasons=reasons)


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
