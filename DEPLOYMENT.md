# CareerMatch — Production Deployment Guide ($0/Month)

This guide documents the automated deployment architecture for **CareerMatch**, a Telegram Mini App for university job recommendations.

The entire stack is designed to run **online 24/7 at $0.00/month recurring cost**, with stable HTTPS URLs, without requiring your MacBook or local terminal to remain open.

---

## 1. Quick Start: One-Command Deployment

Once initial service accounts are linked, you can deploy or update the entire system with:

```bash
./deploy.sh
```

### What `./deploy.sh` Does Automatically:
1. **Validates prerequisites**: Checks `git`, `node`, `pnpm`, `python3`, `curl`, and `vercel` CLI.
2. **Loads private deployment configuration**: Reads from `.deploy.env` (automatically gitignored with restricted `chmod 600` permissions).
3. **Applies database migrations**: Connects securely via SSL to your Neon PostgreSQL database and runs `migrate`.
4. **Seeds initial live jobs**: Ingests fresh humanitarian and NGO vacancies from ReliefWeb if the database is empty (`ingest_reliefweb --pages 5`).
5. **Builds & deploys frontend**: Compiles production assets and deploys to Vercel with your public Render backend URL.
6. **Runs automated verification**: Tests backend `/api/health/`, database connectivity, frontend HTTP 200, and CORS allowlists over HTTPS.
7. **Displays permanent URLs**: Prints the exact URLs for your Telegram Mini App Menu Button.

---

## 2. Architecture Overview

| Component | Provider | Plan | Role |
|---|---|---|---|
| **Frontend** | [Vercel](https://vercel.com/) | Hobby (Free) | React 19 SPA, global edge CDN, permanent HTTPS |
| **Backend** | [Render](https://render.com/) | Free Web Service | Django 6.1 + DRF + Gunicorn + WhiteNoise |
| **Database** | [Neon](https://neon.tech/) | Serverless PostgreSQL (Free) | 0.5 GB permanent storage (does not expire after 30 days) |
| **Jobs Data** | [ReliefWeb](https://api.reliefweb.int/) | Public UN OCHA API (Free) | Real-world job vacancy ingestion |
| **Delivery** | [Telegram Bot](https://core.telegram.org/bots/webapps) | Free | `@careermatch123bot` Mini App Webview |

---

## 3. One-Time Setup (First Run Only)

### Step 1: Create Your Free Database on Neon
1. Go to [Neon Console](https://console.neon.tech/) and sign in with GitHub or email.
2. Click **Create Project**, name it `careermatch`, and select your nearest region.
3. In the connection details modal, select **Pooled connection** and copy the connection string.
   - Example format: `postgresql://user:password@ep-xyz.region.aws.neon.tech/careermatch?sslmode=require`
4. Keep this string private — you will paste it into Render and `./deploy.sh`.

### Step 2: Create Your Backend Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and sign in.
2. Click **New +** → **Web Service** → Connect your GitHub repository `Kimsun369/CareerMatch`.
3. Configure the service settings:
   - **Name**: `careermatch-backend`
   - **Root Directory**: `Backend`
   - **Runtime**: `Python`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn careermatch.wsgi:application --bind 0.0.0.0:$PORT`
   - **Instance Type**: `Free`
4. Add the following **Environment Variables** in Render's Environment tab:
   | Key | Value |
   |---|---|
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_SECRET_KEY` | *(Click "Generate" or type a random 50-character string)* |
   | `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
   | `DATABASE_URL` | *(Your Neon connection string from Step 1)* |
   | `TELEGRAM_BOT_TOKEN` | *(Your bot token from @BotFather)* |
   | `RELIEFWEB_APPNAME` | `careermatch-fyp` |
   | `CORS_ALLOWED_ORIGINS` | `https://careermatch.vercel.app` *(update once Vercel URL is created)* |
   | `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
5. Click **Create Web Service**. Render will run `build.sh` (installing dependencies, collecting static files, and running migrations).
6. Note your Render URL: `https://careermatch-backend.onrender.com`.

### Step 3: Deploy Frontend to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/) and click **Add New...** → **Project**.
2. Import the `CareerMatch` GitHub repository.
3. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click edit and select `Frontend`
   - **Build Command**: `pnpm build` (or `npm run build`)
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://careermatch-backend.onrender.com/api` *(replace with your real Render URL, without trailing slash)*
5. Click **Deploy**. Note your Vercel URL: `https://careermatch.vercel.app`.
6. *(Important)*: Back in Render, ensure `CORS_ALLOWED_ORIGINS` includes this exact Vercel URL.

### Step 4: Link Your Telegram Bot Menu Button
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/setmenubutton`.
3. Select `@careermatch123bot`.
4. Enter the button text: `Open CareerMatch`.
5. Enter your Vercel URL: `https://careermatch.vercel.app`.
6. Open your bot in Telegram and tap the menu button to verify that the Mini App loads directly inside Telegram!

---

## 4. Free-Plan Limitations & Tips for University Demonstration

> [!IMPORTANT]
> **Render Free Web Service Cold Starts:**
> - Render free web services automatically spin down (sleep) after 15 minutes of inactivity.
> - When a user opens the app after inactivity, the first backend request takes **30 to 50 seconds** to wake up.
> - The frontend displays animated skeleton loaders and retry prompts while waiting.
> - **Demo Tip**: 2 to 3 minutes before your university presentation, open the Mini App on your phone or visit `https://<your-service>.onrender.com/api/health/` in your browser. This wakes the service so your presentation runs instantaneously.
> - You can also set up a free monitor on [UptimeRobot](https://uptimerobot.com/) or [Cron-Job.org](https://cron-job.org/) to ping `/api/health/` every 10 minutes to keep it awake during your demonstration day.

> [!NOTE]
> **Neon Serverless PostgreSQL:**
> - Neon does **not** delete databases after 30 days (unlike Render's free PostgreSQL).
> - Neon compute auto-suspends when idle and wakes up in < 1 second upon receiving an SQL query.
> - 0.5 GB storage is permanently free. CareerMatch with 500 active jobs and test users uses under 15 MB.

---

## 5. Automated Daily Job Ingestion ($0/Month via GitHub Actions)

CareerMatch includes a fully automated daily job ingestion pipeline in [`.github/workflows/daily-job-ingestion.yml`](.github/workflows/daily-job-ingestion.yml) that automatically runs without needing any servers or your computer running.

### Key Capabilities:
- **Daily Schedule**: Runs automatically once per day at `00:00 UTC` (`07:00 AM` Cambodia time / ICT).
- **500 Jobs Ingestion**: Ingests up to 500 real humanitarian and NGO jobs per run from the ReliefWeb API.
- **Deduplication & Change Detection**:
  - Enforces database uniqueness on `(source, source_id)`.
  - Filters intra-run duplicates returned across paginated batches.
  - Detects if existing job fields are unchanged and skips redundant database writes.
- **Automatic Stale Cleanup**: Optionally deactivates listings whose closing dates have passed (`is_active=False`).
- **Concurrency Protection**: GitHub Actions concurrency lock prevents multiple runs from overlapping or conflicting.
- **$0.00/Month**: Runs on GitHub's free runners (~30 seconds/day, well under free tier limits) and connects directly to your Neon PostgreSQL database over SSL.

### Setting Up GitHub Actions Secrets (One-Time Setup):
In your GitHub repository (`https://github.com/Kimsun369/CareerMatch`):
1. Go to **Settings** → **Secrets and variables** → **Actions**.
2. Under **Repository secrets**, click **New repository secret** and add:
   - `DATABASE_URL`: Your pooled Neon connection string (`postgresql://user:pass@ep-xyz.region.aws.neon.tech/careermatch?sslmode=require`)
   - `DJANGO_SECRET_KEY`: Your Django secret key (same as Render)
   - `RELIEFWEB_APPNAME`: (Optional) `careermatch-fyp`

### How to Manually Trigger & Monitor Ingestion:
1. In your GitHub repository, click on the **Actions** tab.
2. Select **Daily ReliefWeb Job Ingestion** from the left sidebar.
3. Click **Run workflow**, choose options (e.g. `max_records: 500`, `deactivate_missing: true`), and click **Run workflow**.
4. Click on the active workflow run to view real-time logs and the final summary metrics:
   ```text
   ──────────────────────────────────────────────────
   ReliefWeb Ingestion Summary
   ──────────────────────────────────────────────────
     Requested Max Records : 500
     Total Fetched         : 500
     Valid Normalized      : 494
     Created (New)         : 42
     Updated (Modified)    : 8
     Unchanged (Skipped)   : 444
     Intra-run Duplicates  : 0
     Invalid / Skipped     : 6
     Errors                : 0
     Deactivated Stale     : 12
   ──────────────────────────────────────────────────
     Total Active Jobs in DB: 1,280
   ──────────────────────────────────────────────────
   ```

---

## 6. Security & Safety Checklist

- [x] **No Secrets in Frontend**: `DATABASE_URL` and `TELEGRAM_BOT_TOKEN` exist only on Render and GitHub Secrets.
- [x] **HMAC Signature Verification**: With `DJANGO_DEBUG=False`, Telegram `initData` is cryptographically validated using HMAC-SHA256. Spoofed or tampered headers are rejected.
- [x] **Local Debug Fallback Disabled**: The `X-Debug-Telegram-Id` header is strictly ignored when `DJANGO_DEBUG=False`.
- [x] **Protected by `.gitignore`**: `.deploy.env`, local `.env`, and virtual environments are blocked from Git commits.
- [x] **Zero Recurring Cost**: All services run strictly on verified free tiers ($0/month).


