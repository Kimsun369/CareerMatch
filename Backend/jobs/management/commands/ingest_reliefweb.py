"""Management command: ingest_reliefweb

Fetches real job listings from the ReliefWeb public API, normalises them,
and upserts them into PostgreSQL (Neon).

Usage:
    python manage.py ingest_reliefweb
    python manage.py ingest_reliefweb --max-records 500
    python manage.py ingest_reliefweb --limit 100 --pages 5
    python manage.py ingest_reliefweb --query "project manager"
    python manage.py ingest_reliefweb --deactivate-missing

Scheduled via GitHub Actions daily at 00:00 UTC (07:00 Cambodia time).
"""

from __future__ import annotations

import logging
import math
import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from jobs.models import Job
from jobs.reliefweb import ReliefWebError, fetch_jobs, normalize_all

logger = logging.getLogger(__name__)

# Attributes compared on existing Job records to detect actual changes
CORE_JOB_FIELDS = (
    "title",
    "organization",
    "location",
    "country",
    "job_type",
    "field",
    "description",
    "closing_date",
    "published_date",
    "source_name",
    "source_url",
    "is_active",
)


class Command(BaseCommand):
    help = (
        "Fetch real job listings from the ReliefWeb API, normalise them, and "
        "upsert them into PostgreSQL. Run periodically to keep listings fresh."
    )

    def add_arguments(self, parser):
        default_limit = int(os.environ.get("RELIEFWEB_INGEST_LIMIT", "100"))
        default_pages = int(os.environ.get("RELIEFWEB_INGEST_PAGES", "5"))
        default_max = int(os.environ.get("RELIEFWEB_INGEST_MAX_RECORDS", "500"))

        parser.add_argument(
            "--limit",
            type=int,
            default=default_limit,
            help=f"Records to request per page (max 100, ReliefWeb API limit). Default: {default_limit}.",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=default_pages,
            help=f"Max pages to fetch. Default: {default_pages}.",
        )
        parser.add_argument(
            "--max-records",
            type=int,
            default=default_max,
            help=f"Maximum total jobs to process across pages. Default: {default_max}.",
        )
        parser.add_argument(
            "--query",
            type=str,
            default=None,
            help="Optional ReliefWeb full-text query filter (e.g. 'cambodia ngo').",
        )
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            default=False,
            help=(
                "After ingestion, mark any ReliefWeb jobs whose closing_date "
                "has passed as inactive (is_active=False)."
            ),
        )

    def handle(self, *args, **options):
        limit = max(1, min(options["limit"], 100))  # Hard cap 100 per ReliefWeb API
        max_records = max(1, options["max_records"])
        max_pages = max(1, min(options["pages"], math.ceil(max_records / limit)))
        query = options["query"]

        total_fetched = 0
        total_valid = 0
        created_count = 0
        updated_count = 0
        unchanged_count = 0
        skipped_invalid_count = 0
        intra_run_duplicates = 0
        error_count = 0
        seen_source_ids: set[str] = set()

        self.stdout.write(
            self.style.HTTP_INFO(
                f"Starting ReliefWeb ingestion: target up to {max_records} jobs "
                f"({max_pages} pages × {limit}/page)"
                + (f", query='{query}'" if query else "")
            )
        )

        for page_num in range(max_pages):
            if len(seen_source_ids) >= max_records:
                self.stdout.write(
                    self.style.SUCCESS(f"  Reached target limit of {max_records} records.")
                )
                break

            # Polite pause between pages to respect ReliefWeb API rate limits
            if page_num > 0:
                time.sleep(0.5)

            offset = page_num * limit
            # Adjust limit on final page if remaining needed < limit
            current_limit = min(limit, max_records - len(seen_source_ids))
            if current_limit <= 0:
                break

            self.stdout.write(
                f"  Fetching page {page_num + 1}/{max_pages} (limit={current_limit}, offset={offset})…",
                ending=" ",
            )

            try:
                raw_items = fetch_jobs(limit=current_limit, offset=offset, query=query)
            except ReliefWebError as exc:
                self.stderr.write(self.style.ERROR(f"FAILED: {exc}"))
                raise CommandError(f"ReliefWeb ingestion failed: {exc}") from exc

            if not raw_items:
                self.stdout.write(self.style.WARNING("no more records — stopping early."))
                break

            total_fetched += len(raw_items)
            normalised = normalize_all(raw_items)
            page_invalid = len(raw_items) - len(normalised)
            skipped_invalid_count += page_invalid
            total_valid += len(normalised)

            page_created = 0
            page_updated = 0
            page_unchanged = 0
            page_duplicates = 0
            page_errors = 0

            for item in normalised:
                if len(seen_source_ids) >= max_records:
                    break

                source_id = item["source_id"]
                if source_id in seen_source_ids:
                    page_duplicates += 1
                    intra_run_duplicates += 1
                    continue
                seen_source_ids.add(source_id)

                try:
                    existing = Job.objects.filter(
                        source=item["source"], source_id=source_id
                    ).first()

                    if existing is None:
                        # New job record
                        Job.objects.create(**item)
                        page_created += 1
                    else:
                        # Check if any core fields actually changed
                        has_changes = False
                        for field_name in CORE_JOB_FIELDS:
                            if getattr(existing, field_name) != item.get(field_name):
                                has_changes = True
                                setattr(existing, field_name, item.get(field_name))

                        if has_changes:
                            existing.raw_metadata = item.get("raw_metadata", existing.raw_metadata)
                            existing.save()
                            page_updated += 1
                        else:
                            page_unchanged += 1

                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to persist job source_id=%s: %s", source_id, exc)
                    page_errors += 1

            created_count += page_created
            updated_count += page_updated
            unchanged_count += page_unchanged
            error_count += page_errors

            self.stdout.write(
                f"fetched {len(raw_items)}, "
                f"created {page_created}, "
                f"updated {page_updated}, "
                f"unchanged {page_unchanged}, "
                f"skipped invalid {page_invalid}"
                + (f", duplicates {page_duplicates}" if page_duplicates else "")
                + (f", errors {page_errors}" if page_errors else "")
            )

        # ── Optional: deactivate stale jobs ──────────────────────────────────
        deactivated = 0
        if options["deactivate_missing"]:
            today = timezone.now().date()
            stale_qs = Job.objects.filter(
                source="reliefweb",
                is_active=True,
                closing_date__lt=today,
            )
            deactivated = stale_qs.update(is_active=False)
            if deactivated:
                self.stdout.write(
                    self.style.WARNING(f"  Deactivated {deactivated} job(s) past their closing date.")
                )

        # ── Summary ───────────────────────────────────────────────────────────
        separator = "─" * 50
        self.stdout.write(separator)
        self.stdout.write(self.style.SUCCESS("ReliefWeb Ingestion Summary"))
        self.stdout.write(separator)
        self.stdout.write(f"  Requested Max Records : {max_records}")
        self.stdout.write(f"  Total Fetched         : {total_fetched}")
        self.stdout.write(f"  Valid Normalized      : {total_valid}")
        self.stdout.write(f"  Created (New)         : {created_count}")
        self.stdout.write(f"  Updated (Modified)    : {updated_count}")
        self.stdout.write(f"  Unchanged (Skipped)   : {unchanged_count}")
        self.stdout.write(f"  Intra-run Duplicates  : {intra_run_duplicates}")
        self.stdout.write(f"  Invalid / Skipped     : {skipped_invalid_count}")
        self.stdout.write(f"  Errors                : {error_count}")
        if options["deactivate_missing"]:
            self.stdout.write(f"  Deactivated Stale     : {deactivated}")
        self.stdout.write(separator)

        total_active = Job.objects.filter(is_active=True).count()
        self.stdout.write(f"  Total Active Jobs in DB: {total_active}")
        self.stdout.write(separator)

        if error_count > 0:
            self.stderr.write(
                self.style.ERROR(
                    f"\n{error_count} error(s) occurred during ingestion. "
                    "Check the logs for details."
                )
            )
