# CareerMatch — Guide

A step-by-step walkthrough for getting this project running, understanding
how it's put together, and configuring the pieces that need your own
credentials.

---

## 1. Prerequisites

You only need **Docker** (Docker Desktop on Mac/Windows, or Docker Engine
on Linux) for the one-command path in section 2.

For the manual path in section 3, you'll instead need:
- Python 3.12+
- Node 20+ with `pnpm` (`corepack enable` if you don't have it)
- PostgreSQL, if you want real persistence (SQLite is used automatically
  if you skip this)

---

## 2. Fastest path: one command

```bash
cd "Career Match"
docker compose up --build
```

This starts three containers, in dependency order:

1. **`db`** — PostgreSQL 16, with a health check so nothing else starts
   until it's actually accepting connections.
2. **`backend`** — waits for Postgres, runs `python manage.py migrate`
   automatically, then serves Django on `http://localhost:8000`.
3. **`frontend`** — installs dependencies and serves the Vite dev server
   on `http://localhost:8443`.

First run takes a minute or two (building images, installing
dependencies). Open **http://localhost:8443** once it's up.

Stop with `Ctrl+C`. Run `docker compose down` to fully stop the
containers, or `docker compose down -v` to also delete the Postgres data
volume and start fresh next time.

### Loading real job listings

The app runs and shows correct empty states with zero jobs in the
database — that's expected on a fresh install. To pull real listings from
ReliefWeb, with `docker compose up` still running, in a second terminal:

```bash
docker compose exec backend python manage.py ingest_reliefweb --pages 3
```

Increase `--pages` for more jobs (each page is ~20-100 listings depending
on ReliefWeb's response). Run it again any time to pick up new postings —
it updates existing jobs and skips exact duplicates rather than
re-creating them.

This step needs outbound internet access to `api.reliefweb.int`.

---

## 3. Manual path (no Docker)

Two terminals, run at the same time.

**Terminal 1 — backend:**

```bash
cd "Career Match/Backend"
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If `DATABASE_URL` in `.env` isn't reachable (e.g. you don't have a local
Postgres running), the backend automatically falls back to a local
`db.sqlite3` file — fine for a quick look, not recommended for anything
beyond that.

**Terminal 2 — frontend:**

```bash
cd "Career Match/Frontend"
pnpm install
pnpm dev
```

Vite will print the URL it's serving on (defaults to
`http://localhost:8443`, configured in `vite.config.ts`).

---

## 4. What's pre-configured vs. what you must supply

### Already set up for you

| File | What's in it |
|---|---|
| `Backend/.env` | A real, generated Django secret key; SQLite/Postgres wiring; CORS already pointing at the frontend's dev port; a placeholder `RELIEFWEB_APPNAME`. |
| `Frontend/.env` | `VITE_API_BASE_URL` pointed at `http://localhost:8000/api`. |

`RELIEFWEB_APPNAME` doesn't need registration — ReliefWeb just asks every
API consumer to identify itself with a short slug. The placeholder
(`careermatch-fyp`) works as-is, or change it to your own project name.

### You need to supply these yourself

These are real third-party credentials. Nothing fake has been put in
their place — the app is built to work correctly without them, per the
project's own requirement that AI stays optional and Telegram identity
never falls back to a fake login form in production.

| Variable | Where | Required? | Get it from |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `Backend/.env` | Only for real Telegram Mini App deployment | [@BotFather](https://t.me/BotFather) on Telegram |
| `GROQ_API_KEY` | `Backend/.env` | Fully optional | [console.groq.com](https://console.groq.com) |

Without `TELEGRAM_BOT_TOKEN`, the app works completely normally in an
ordinary browser — see section 5.

---

## 5. How identity works (important to understand)

CareerMatch has no username/password login. Identity comes from Telegram.

- **Inside real Telegram**: the frontend (`Frontend/src/telegram.ts`)
  reads the signed `initData` string Telegram's WebApp SDK provides, and
  sends it on every API request as the `X-Telegram-Init-Data` header.
  Django (`Backend/users/telegram_auth.py`) verifies its HMAC signature
  against `TELEGRAM_BOT_TOKEN` before trusting it.
- **In an ordinary browser** (your default dev experience, no Telegram
  needed): there's no `initData` to send, so the frontend instead sends a
  `X-Debug-Telegram-Id` header — a random id it generates once and
  remembers in `localStorage`, so the same "user" persists across
  reloads. The backend only accepts this header when `DJANGO_DEBUG=True`,
  so it can never accidentally become the production path.

You don't need to do anything to use the dev fallback — it's automatic.

---

## 6. Everyday commands

| Task | Docker | Manual |
|---|---|---|
| Start everything | `docker compose up` | run backend + frontend in two terminals |
| Rebuild after dependency changes | `docker compose up --build` | `pip install -r requirements.txt` / `pnpm install` |
| Run a Django management command | `docker compose exec backend python manage.py <cmd>` | `python manage.py <cmd>` |
| Create a Django admin user | `docker compose exec backend python manage.py createsuperuser` | `python manage.py createsuperuser` |
| View backend logs | `docker compose logs -f backend` | visible directly in the terminal |
| Reset the database | `docker compose down -v` then `docker compose up` | delete `db.sqlite3` (SQLite) or drop/recreate the Postgres DB |
| Ingest ReliefWeb jobs | `docker compose exec backend python manage.py ingest_reliefweb --pages 3` | `python manage.py ingest_reliefweb --pages 3` |

The Django admin site is available at `http://localhost:8000/admin/`
after creating a superuser — useful for eyeballing ingested jobs,
preferences, and saved jobs directly.

---

## 7. Project layout

```
Career Match/
├── docker-compose.yml       one-command orchestration
├── README.md                 quick-start summary
├── GUIDE.md                  this file
├── Backend/                  Django + DRF + PostgreSQL
│   ├── careermatch/          project settings, root URLs
│   ├── users/                TelegramUser model, Telegram auth, profile API
│   ├── jobs/                 Job/SavedJob/UserPreference models,
│   │                         ReliefWeb ingestion, recommendation engine,
│   │                         job/recommendation/saved-job API
│   ├── .env                  real working local config
│   └── Dockerfile
└── Frontend/                 Vite + React + TypeScript
    ├── src/
    │   ├── App.tsx            all screens (onboarding, feed, job detail,
    │   │                       saved jobs, profile)
    │   ├── api.ts              centralized API client
    │   ├── telegram.ts         Telegram WebApp SDK integration
    │   └── types.ts            shared TypeScript types
    ├── .env                    real working local config
    └── Dockerfile
```

---

## 8. If something goes wrong

- **`docker compose up` fails pulling images** — check your own network/
  Docker Hub access; this doesn't depend on anything in the project
  config.
- **Frontend loads but shows connection errors** — confirm the backend
  is actually up (`http://localhost:8000/api/jobs/` should return JSON,
  not a connection refused) and that `Frontend/.env`'s
  `VITE_API_BASE_URL` matches where it's running.
- **CORS errors in the browser console** — the frontend's origin needs
  to be listed in `Backend/.env`'s `CORS_ALLOWED_ORIGINS`. The default
  already covers Vite's usual ports (8443, 5173) on both `localhost` and
  `127.0.0.1`.
- **Recommendations endpoint returns 409** — this is correct behavior: it
  means onboarding hasn't been completed for that user yet. Complete the
  onboarding flow in the UI first.
- **Ingestion command fails with a `RELIEFWEB_APPNAME` error** — check
  `Backend/.env` still has a value set for it (a placeholder ships by
  default, so this should only happen if it was cleared).

If you hit an error not covered here, send me the exact message and I'll
fix it.
