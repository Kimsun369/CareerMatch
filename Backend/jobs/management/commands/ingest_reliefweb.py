"""Management command: ingest_reliefweb

Fetches real job listings from the ReliefWeb public API, normalises them,
and upserts them into PostgreSQL.

Usage:
    python manage.py ingest_reliefweb
    python manage.py ingest_reliefweb --limit 50 --pages 3
    python manage.py ingest_reliefweb --query "project manager cambodia"
    python manage.py ingest_reliefweb --deactivate-missing

Expected successful output:
    Page 1/5: fetched 100 raw reports, 95 valid after normalisation.
    Page 2/5: fetched 100 raw reports, 98 valid after normalisation.
    ...
    ─────────────────────────────────────────
    Ingestion complete.
      Created : 180
      Updated : 95
      Skipped :  8  (missing title or url)
      Errors  :  0
    ─────────────────────────────────────────

If RELIEFWEB_APPNAME is not set, it defaults to "careermatch-fyp".
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from jobs.models import Job
from jobs.reliefweb import ReliefWebError, fetch_jobs, normalize_all

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Fetch real job listings from the ReliefWeb API, normalise them, and "
        "upsert them into PostgreSQL. Run periodically to keep listings fresh."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Records to request per page (max 100, ReliefWeb API limit).",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=5,
            help="How many pages to fetch (total records = limit × pages).",
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
        limit = min(options["limit"], 100)  # Hard cap per ReliefWeb
        pages = options["pages"]
        query = options["query"]

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        seen_source_ids: set[str] = set()

        self.stdout.write(
            self.style.HTTP_INFO(
                f"Starting ReliefWeb ingestion: {pages} page(s) × {limit} records/page"
                + (f", query='{query}'" if query else "")
            )
        )

        for page_num in range(pages):
            offset = page_num * limit
            self.stdout.write(f"  Fetching page {page_num + 1}/{pages} (offset={offset})…", ending=" ")

            try:
                raw_items = fetch_jobs(limit=limit, offset=offset, query=query)
            except ReliefWebError as exc:
                # Fail loudly — never silently fall back to no/fake data.
                raise CommandError(f"ReliefWeb ingestion failed: {exc}") from exc

            if not raw_items:
                self.stdout.write(self.style.WARNING("no more records — stopping early."))
                break

            normalised = normalize_all(raw_items)
            page_skipped = len(raw_items) - len(normalised)
            skipped_count += page_skipped

            page_created = 0
            page_updated = 0
            page_errors = 0

            for item in normalised:
                source_id = item["source_id"]
                if source_id in seen_source_ids:
                    # Duplicate within this ingestion run (ReliefWeb can return
                    # overlapping pages) — skip without counting as an error.
                    continue
                seen_source_ids.add(source_id)

                try:
                    _, was_created = Job.objects.update_or_create(
                        source=item["source"],
                        source_id=source_id,
                        defaults={k: v for k, v in item.items() if k not in ("source", "source_id")},
                    )
                    if was_created:
                        page_created += 1
                    else:
                        page_updated += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to upsert job source_id=%s: %s", source_id, exc)
                    page_errors += 1

            created_count += page_created
            updated_count += page_updated
            error_count += page_errors

            self.stdout.write(
                f"fetched {len(raw_items)}, "
                f"created {page_created}, "
                f"updated {page_updated}, "
                f"skipped {page_skipped}"
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
            self.stdout.write(
                self.style.WARNING(f"  Deactivated {deactivated} job(s) past their closing date.")
            )

        # ── Summary ───────────────────────────────────────────────────────────
        separator = "─" * 45
        self.stdout.write(separator)
        self.stdout.write(
            self.style.SUCCESS("Ingestion complete.") + "\n"
            + f"  Created   : {created_count}\n"
            + f"  Updated   : {updated_count}\n"
            + f"  Skipped   : {skipped_count}  (missing title or url)\n"
            + f"  Errors    : {error_count}\n"
            + (f"  Deactivated: {deactivated}\n" if options["deactivate_missing"] else "")
        )
        self.stdout.write(separator)

        total = Job.objects.filter(is_active=True).count()
        self.stdout.write(f"  Active jobs in database: {total}")

        if error_count:
            self.stderr.write(
                self.style.ERROR(
                    f"\n{error_count} error(s) occurred during ingestion. "
                    "Check the logs for details."
                )
            )
