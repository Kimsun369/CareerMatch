"""ReliefWeb ingestion adapter.

Architecture:
    ReliefWeb API  →  fetch_jobs()  →  normalize_job()  →  Job model

This module is intentionally isolated so a second data source can be added
behind its own adapter without touching the Job schema or other app code.

API docs: https://apidoc.rwlabs.org/

The ReliefWeb API uses POST requests with a JSON body to specify which fields
to return (the "fields" parameter) and how to sort/filter results. We call
the v2 jobs endpoint with a POST body.

All public functions raise ``ReliefWebError`` on network/API failure.
Callers MUST NOT substitute fake/cached data on error.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Iterable

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ReliefWeb v2 jobs endpoint (POST with JSON body).
RELIEFWEB_ENDPOINT = "https://api.reliefweb.int/v2/jobs"

# Fields to request from ReliefWeb. We only ask for what we need to keep the
# response payload small. Refer to https://apidoc.rwlabs.org/ for field names.
FIELDS_INCLUDE = [
    "title",
    "body",
    "url",
    "url_alias",
    "date.created",
    "date.closing",
    "source.name",
    "country.name",
    "career_categories.name",
    "type.name",
    # Note: "job_experience.name" is NOT a valid ReliefWeb v2 field — removed.
]

# ── Mapping tables ────────────────────────────────────────────────────────────

# ReliefWeb "type of job" → our job_type taxonomy.
# ReliefWeb postings are overwhelmingly paid full-time roles; internships and
# volunteer positions are tagged explicitly when they are not.
_JOB_TYPE_MAP: dict[str, str] = {
    "job": "full_time",
    "internship": "internship",
    "volunteer opportunity": "freelance",
    "consultancy": "freelance",
    "contract": "full_time",
    "part-time": "part_time",
}

# ReliefWeb career_categories.name → our field taxonomy.
# ReliefWeb's categories are humanitarian-sector specific; most map to
# "health_ngo" — a handful map more precisely to other onboarding fields.
_FIELD_MAP: dict[str, str] = {
    # Tech & IT
    "information & communications technology": "tech_it",
    "information and communications technology": "tech_it",
    "ict": "tech_it",
    # Logistics & Supply Chain
    "logistics/procurement": "logistics_supply_chain",
    "logistics and procurement": "logistics_supply_chain",
    "supply chain": "logistics_supply_chain",
    # Education & Teaching
    "education": "education_teaching",
    # Finance & Banking
    "finance": "finance_banking",
    "administration/finance": "finance_banking",
    # Marketing & Sales / Communications
    "communication": "marketing_sales",
    "advocacy/communications": "marketing_sales",
    "media and communications": "marketing_sales",
    # Construction & Engineering
    "engineering": "construction_engineering",
    "shelter and non-food items": "construction_engineering",
    "wash and sanitation": "construction_engineering",
    # Health & NGO (catch-all for humanitarian sector roles)
    "health": "health_ngo",
    "nutrition": "health_ngo",
    "protection": "health_ngo",
    "coordination": "health_ngo",
    "human resources": "health_ngo",
    "monitoring and evaluation": "health_ngo",
    "programme and project management": "health_ngo",
    "food and nutrition": "health_ngo",
    "disaster management": "health_ngo",
    "mine action": "health_ngo",
    "camp coordination and camp management": "health_ngo",
}


class ReliefWebError(Exception):
    """Raised when the ReliefWeb API call fails or returns an unexpected response."""


def fetch_jobs(
    limit: int = 100,
    offset: int = 0,
    query: str | None = None,
) -> list[dict]:
    """Call the ReliefWeb API and return the raw list of job report dicts.

    Args:
        limit:  Number of records to fetch (max 100 per ReliefWeb's API limit).
        offset: Zero-based record offset for pagination.
        query:  Optional full-text filter string (passed as ReliefWeb query).

    Returns:
        List of raw report dicts from the ReliefWeb ``data`` array.

    Raises:
        ReliefWebError: on network failure, HTTP error, or unexpected response shape.
    """
    # appname is required as a URL query parameter by the ReliefWeb API.
    # The FYP proposal endpoint shows: ?appname=KhmerGigs-TelegramMiniApp-X7K29
    appname = (
        getattr(settings, "RELIEFWEB_APPNAME", "") or "KhmerGigs-TelegramMiniApp-X7K29"
    )

    # appname goes in the URL query string — NOT in the POST body.
    query_params = {"appname": appname}

    body: dict = {
        "limit": min(limit, 100),  # ReliefWeb hard caps at 100
        "offset": offset,
        "sort": ["date.created:desc"],
        "fields": {"include": FIELDS_INCLUDE},
        "filter": {
            "field": "status",
            "value": "published",
        },
    }
    if query:
        body["query"] = {"value": query, "operator": "AND"}

    try:
        response = requests.post(
            RELIEFWEB_ENDPOINT,
            params=query_params,   # appname in URL: ?appname=...
            json=body,             # rest of query in POST body
            timeout=30,
            headers={"User-Agent": f"CareerMatch-FYP/{appname}"},
        )
    except requests.Timeout:
        raise ReliefWebError("Request to ReliefWeb timed out after 30 seconds.")
    except requests.ConnectionError as exc:
        raise ReliefWebError(f"Could not connect to ReliefWeb: {exc}") from exc
    except requests.RequestException as exc:
        raise ReliefWebError(f"Network error contacting ReliefWeb: {exc}") from exc

    if response.status_code != 200:
        raise ReliefWebError(
            f"ReliefWeb returned HTTP {response.status_code}: {response.text[:500]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise ReliefWebError("ReliefWeb response was not valid JSON.") from exc

    items = data.get("data")
    if items is None:
        raise ReliefWebError(
            f"Unexpected ReliefWeb response shape: missing 'data' key. "
            f"Response preview: {str(data)[:300]}"
        )

    return items


def _parse_date(value: str | None) -> dt.date | None:
    """Parse an ISO-8601 date string; returns None for empty/invalid input."""
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def _guess_job_type(type_names: list[str]) -> str | None:
    """Map a list of ReliefWeb type.name values to our job_type taxonomy.

    Returns the first matching code, or "full_time" as the safe default when
    type_names is non-empty (most ReliefWeb listings are full-time roles even
    when unlabelled). Returns None only when the list is empty.
    """
    for name in type_names:
        mapped = _JOB_TYPE_MAP.get(name.strip().lower())
        if mapped:
            return mapped
    # Non-empty list but no recognised type → assume full-time (most common).
    return "full_time" if type_names else None


def _guess_field(category_names: list[str]) -> str | None:
    """Map ReliefWeb career_categories.name values to our field taxonomy.

    Returns the first matching code. Returns None when no match is found
    (we never force an unknown job into a category — unknown stays unknown).
    """
    for name in category_names:
        mapped = _FIELD_MAP.get(name.strip().lower())
        if mapped:
            return mapped
    return None


def normalize_job(raw: dict) -> dict | None:
    """Convert one raw ReliefWeb report into Job model kwargs.

    Returns None if the record is missing essential fields (title or url) —
    such records are skipped entirely rather than stored with invented data.
    All optional fields are handled safely; missing data maps to null/None.
    """
    try:
        fields = raw.get("fields", {}) or {}
        title = (fields.get("title") or "").strip()
        url = (fields.get("url") or fields.get("url_alias") or "").strip()

        if not title or not url:
            logger.warning(
                "Skipping ReliefWeb report %s: missing title or url",
                raw.get("id"),
            )
            return None

        sources = fields.get("source") or []
        countries = fields.get("country") or []
        categories = fields.get("career_categories") or []
        types = fields.get("type") or []

        organization = sources[0]["name"] if sources else None
        country = countries[0]["name"] if countries else None

        category_names = [c["name"] for c in categories if c.get("name")]
        type_names = [t["name"] for t in types if t.get("name")]

        dates = fields.get("date") or {}
        body = (fields.get("body") or "").strip()

        return {
            "source": "reliefweb",
            "source_id": str(raw["id"]),
            "title": title,
            "organization": organization,
            # ReliefWeb job reports rarely give city-level location; country
            # is used for both 'location' and 'country' fields.
            "location": country,
            "country": country,
            "job_type": _guess_job_type(type_names),
            "field": _guess_field(category_names),
            "description": body,
            "skills": [],  # ReliefWeb has no structured skills list
            "closing_date": _parse_date(dates.get("closing")),
            "published_date": _parse_date(dates.get("created")),
            "source_name": "ReliefWeb",
            "source_url": url,
            "raw_metadata": raw,
            "is_active": True,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Unexpected error normalising ReliefWeb report %s: %s",
            raw.get("id"),
            exc,
        )
        return None


def normalize_all(raw_items: Iterable[dict]) -> list[dict]:
    """Normalise a sequence of raw ReliefWeb reports, silently dropping failures."""
    normalized = []
    for raw in raw_items:
        item = normalize_job(raw)
        if item is not None:
            normalized.append(item)
    return normalized
