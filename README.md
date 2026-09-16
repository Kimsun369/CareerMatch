# CareerMatch — Backend

Django REST Framework backend for the CareerMatch Telegram Mini App FYP.

**Architecture:**
```
ReliefWeb API → Django ingestion → PostgreSQL → DRF API → Next.js Mini App
                                                       ↑
                                             Rule-based recommendation engine
```

---

## Quick Start (Local Development)

### 1. Prerequisites

- Python 3.12+ (project targets Python 3.12–3.14)
- PostgreSQL 14+ running locally
- `pip` (or `pip3`)

### 2. PostgreSQL Setup

Run these once to create the local database and user:

```bash
psql postgres -c "CREATE USER careermatch WITH PASSWORD 'careermatch';"
psql postgres -c "CREATE DATABASE careermatch OWNER careermatch;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE careermatch TO careermatch;"
```

Or on some systems (e.g. macOS with Homebrew):

```bash
createuser -P careermatch        # enter password: careermatch
createdb -O careermatch careermatch
```

### 3. Install Dependencies

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment

The `.env` file is already pre-filled with working local-dev values.
If you need to regenerate it:

```bash
cp .env.example .env
# Edit .env and set your values
```

Minimum required values (already set in `.env`):

```env
DATABASE_URL=postgres://careermatch:careermatch@localhost:5432/careermatch
DJANGO_SECRET_KEY=<any long random string>
RELIEFWEB_APPNAME=careermatch-fyp
```

### 5. Run Migrations

```bash
python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, jobs, sessions, users
Running migrations:
  Applying users.0001_initial... OK
  Applying users.0002_telegramuser_last_name... OK
  Applying jobs.0001_initial... OK
  Applying jobs.0002_userpreference_location_type_default_job_country_idx... OK
  ...
```

### 6. Create a Django Superuser (for Admin)

```bash
python manage.py createsuperuser
```

Then visit `http://127.0.0.1:8000/admin/` to inspect Users, Jobs, and SavedJobs.

### 7. Ingest Real Jobs from ReliefWeb

```bash
python manage.py ingest_reliefweb
```

Expected successful output:
```
Starting ReliefWeb ingestion: 5 page(s) × 100 records/page
  Fetching page 1/5 (offset=0)… fetched 100, created 98, updated 0, skipped 2
  Fetching page 2/5 (offset=100)… fetched 100, created 99, updated 0, skipped 1
  ...
─────────────────────────────────────────────────────────
Ingestion complete.
  Created   : 480
  Updated   : 0
  Skipped   : 12  (missing title or url)
  Errors    : 0
─────────────────────────────────────────────────────────
  Active jobs in database: 480
```

Options:
```bash
# Fetch fewer records (faster for testing)
python manage.py ingest_reliefweb --limit 20 --pages 1

# Filter by keyword
python manage.py ingest_reliefweb --query "cambodia ngo"

# Also deactivate jobs past their closing date
python manage.py ingest_reliefweb --deactivate-missing
```

### 8. Start the Backend Server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`.

---

## API Reference

All endpoints require authentication. In local development, send:
```
X-Debug-Telegram-Id: 12345
```
(any numeric ID; Django will create a test user automatically when `DJANGO_DEBUG=True`)

In real Telegram, the frontend automatically sends the signed `initData` via `X-Telegram-Init-Data`.

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs/` | Paginated job list |
| `GET` | `/api/jobs/?search=keyword` | Keyword search |
| `GET` | `/api/jobs/?job_type=full_time` | Filter by type |
| `GET` | `/api/jobs/?field=tech_it` | Filter by field |
| `GET` | `/api/jobs/?location=Cambodia` | Filter by country |
| `GET` | `/api/jobs/{id}/` | Job detail |
| `GET` | `/api/jobs/recommendations/` | Personalised recommendations |
| `GET` | `/api/jobs/saved/` | User's saved jobs |
| `POST` | `/api/jobs/{id}/save/` | Save/bookmark a job |
| `DELETE` | `/api/jobs/{id}/save/` | Unsave a job |

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/profile/` | User profile + preferences |
| `GET` | `/api/profile/preferences/` | Preferences only |
| `PUT` | `/api/profile/preferences/` | Save/update preferences |
| `POST` | `/api/profile/preferences/` | Alias for PUT |
| `GET` | `/api/profile/saved/` | User's saved jobs (alias) |

### Example: Test Recommendations

```bash
# 1. Save preferences
curl -X PUT http://127.0.0.1:8000/api/profile/preferences/ \
  -H "Content-Type: application/json" \
  -H "X-Debug-Telegram-Id: 12345" \
  -d '{"job_types": ["full_time"], "fields": ["tech_it"], "location_type": "cambodia"}'

# 2. Get recommendations
curl http://127.0.0.1:8000/api/jobs/recommendations/ \
  -H "X-Debug-Telegram-Id: 12345"
```

Example recommendation response:
```json
{
  "results": [
    {
      "id": 1,
      "title": "IT Project Manager",
      "organization": "UNICEF",
      "country": "Cambodia",
      "job_type": "full_time",
      "field": "tech_it",
      "closing_date": "2026-10-31",
      "source_url": "https://reliefweb.int/job/...",
      "match_score": 100,
      "match_reason": "Matches your interest in Tech & IT. Matches your interest in Full-time job. Matches your preferred location (Cambodia).",
      "is_saved": false
    }
  ],
  "count": 1
}
```

---

## Running Tests

```bash
python manage.py test
```

To run a specific test class:
```bash
python manage.py test jobs.tests.RecommendationScoringTests
python manage.py test jobs.tests.RecommendationsAPITests
python manage.py test jobs.tests.SavedJobAPITests
```

All tests use an in-memory SQLite database — no PostgreSQL needed for tests.

---

## Scoring Algorithm

The recommendation engine scores jobs out of 100 points:

| Dimension | Full match | Neutral (unknown field) | Mismatch |
|-----------|-----------|------------------------|----------|
| Job type  | 40 pts    | 20 pts                 | 0 pts    |
| Field     | 40 pts    | 20 pts                 | 0 pts    |
| Location  | 20 pts    | 10 pts                 | 0 pts    |

**Key principle:** Missing/unknown fields on a job are NEUTRAL, not penalising.
A job with no recorded type can still score up to 80 points (field + location).

---

## Identity & Authentication

### Real Telegram (production path)
The frontend sends `initData` from Telegram's WebApp SDK via:
```
X-Telegram-Init-Data: <signed initData string>
```
Django verifies the HMAC-SHA256 signature against `TELEGRAM_BOT_TOKEN`.
Requires `TELEGRAM_BOT_TOKEN` to be set in `.env`.

### Local development (browser/curl)
When `DJANGO_DEBUG=True`, pass:
```
X-Debug-Telegram-Id: <any numeric id>
```
Django creates a `TelegramUser` automatically for that ID.
This path is **disabled** when `DJANGO_DEBUG=False`.

---

## Frontend Integration

The Next.js frontend should set in its `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

The frontend at `http://localhost:8443` (or `:3000` for Next.js) is already
in `CORS_ALLOWED_ORIGINS` in the backend `.env`.

---

## Project Structure

```
Backend/
├── .env                          # Local dev environment (gitignored in prod)
├── .env.example                  # Template — copy to .env
├── manage.py
├── requirements.txt
├── careermatch/                  # Django project config
│   ├── settings.py               # All config via environment variables
│   └── urls.py                   # Root URL config
├── users/                        # User identity app
│   ├── models.py                 # TelegramUser
│   ├── telegram_auth.py          # HMAC verification + DRF auth class
│   ├── permissions.py            # IsTelegramUser permission
│   ├── views.py                  # Profile, Preferences, SavedJobs
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
└── jobs/                         # Jobs + recommendations app
    ├── models.py                 # Job, UserPreference, SavedJob
    ├── serializers.py            # DRF serialisers
    ├── views.py                  # All job endpoints
    ├── urls.py
    ├── recommendation.py         # Rule-based scoring engine
    ├── reliefweb.py              # ReliefWeb API adapter + normalisation
    ├── admin.py
    ├── tests.py                  # Comprehensive test suite
    ├── migrations/
    └── management/
        └── commands/
            └── ingest_reliefweb.py
```

---

## Docker (alternative)

If you have Docker installed, you can run everything with one command:

```bash
cd ..   # go to the CareerMatch root folder
docker compose up --build
```

Then in a second terminal to ingest jobs:
```bash
docker compose exec backend python manage.py ingest_reliefweb --pages 3
```

---

## Troubleshooting

**`django.db.OperationalError: could not connect to server`**
→ PostgreSQL is not running. Start it: `brew services start postgresql` (macOS)

**`403 Forbidden` on all API calls from browser**
→ Make sure your frontend URL is in `CORS_ALLOWED_ORIGINS` in `.env`

**`409 Conflict` from `/api/jobs/recommendations/`**
→ The user hasn't saved preferences yet. POST/PUT to `/api/profile/preferences/` first.

**Empty results from `/api/jobs/recommendations/`**
→ Run `python manage.py ingest_reliefweb` to populate the database.

**`RELIEFWEB_APPNAME is not configured`** error during ingestion
→ Set `RELIEFWEB_APPNAME=careermatch-fyp` in your `.env` file.
# CareerMatch
