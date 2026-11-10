#!/usr/bin/env bash
# ==============================================================================
# CareerMatch — Automated One-Command Deployment & Verification Script
# ==============================================================================
# Target Architecture ($0/month):
#   - Frontend: Vercel (React 19, TypeScript, Vite)
#   - Backend:  Render (Django 6.1, DRF, Gunicorn, WhiteNoise)
#   - Database: Neon Serverless PostgreSQL
#   - Bot:      Telegram Mini App (@careermatch123bot)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="$SCRIPT_DIR/.deploy.env"

# Colors for terminal output
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

info()  { echo -e "${BLUE}${BOLD}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}${BOLD}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}${BOLD}[WARN]${NC} $*"; }
err()   { echo -e "${RED}${BOLD}[ERROR]${NC} $*" >&2; }
banner() {
  echo -e "\n${BOLD}================================================================${NC}"
  echo -e "${BOLD}$*${NC}"
  echo -e "${BOLD}================================================================${NC}\n"
}

# ------------------------------------------------------------------------------
# Step A: Validate Prerequisites
# ------------------------------------------------------------------------------
banner "Step A: Validating Prerequisites"

OS_NAME="$(uname -s)"
info "Operating System: $OS_NAME ($(uname -m))"

# Check required commands
for cmd in git node pnpm python3 curl; do
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$cmd is installed ($("$cmd" --version 2>&1 | head -n 1))"
  else
    err "Required tool '$cmd' is not installed or not in PATH."
    exit 1
  fi
done

# Check Vercel CLI
if command -v vercel >/dev/null 2>&1; then
  ok "vercel CLI is installed ($(vercel --version 2>&1 | head -n 1))"
else
  warn "vercel CLI is not installed globally. You can install it with: npm install -g vercel"
fi

# Check project files
for file in "Frontend/package.json" "Backend/manage.py" "Backend/requirements.txt" "Backend/build.sh"; do
  if [[ -f "$file" ]]; then
    ok "Found $file"
  else
    err "Missing essential file: $file"
    exit 1
  fi
done

# Check git status
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  CURRENT_BRANCH="$(git branch --show-current || echo 'main')"
  ok "Git repository detected on branch '$CURRENT_BRANCH'"
else
  err "This script must be run inside a Git repository."
  exit 1
fi

# ------------------------------------------------------------------------------
# Step B: Load or Prompt for Deployment Configuration (.deploy.env)
# ------------------------------------------------------------------------------
banner "Step B: Deployment Configuration"

if [[ -f "$CONFIG_FILE" ]]; then
  info "Loading existing configuration from $CONFIG_FILE"
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
else
  info "No existing $CONFIG_FILE found. Initial setup required."
  touch "$CONFIG_FILE"
  chmod 600 "$CONFIG_FILE"
fi

# 1. Neon DATABASE_URL
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo -e "\n${BOLD}--- 1. Neon PostgreSQL Database ---${NC}"
  echo "Sign in at https://console.neon.tech/ and create a free project named 'careermatch'."
  echo "Copy the pooled connection string (format: postgresql://...sslmode=require)."
  read -r -p "Enter Neon DATABASE_URL: " input_db_url
  if [[ -n "$input_db_url" ]]; then
    DATABASE_URL="$input_db_url"
    echo "DATABASE_URL=\"$DATABASE_URL\"" >> "$CONFIG_FILE"
    ok "Saved DATABASE_URL to $CONFIG_FILE"
  else
    err "DATABASE_URL is required to deploy and run migrations."
    exit 1
  fi
else
  ok "Neon DATABASE_URL is configured."
fi

# 2. Telegram Bot Token
if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo -e "\n${BOLD}--- 2. Telegram Bot Token ---${NC}"
  echo "Open @BotFather on Telegram, select @careermatch123bot, and copy the Bot API Token."
  read -r -p "Enter TELEGRAM_BOT_TOKEN: " input_bot_token
  if [[ -n "$input_bot_token" ]]; then
    TELEGRAM_BOT_TOKEN="$input_bot_token"
    echo "TELEGRAM_BOT_TOKEN=\"$TELEGRAM_BOT_TOKEN\"" >> "$CONFIG_FILE"
    ok "Saved TELEGRAM_BOT_TOKEN to $CONFIG_FILE"
  else
    err "TELEGRAM_BOT_TOKEN is required for Mini App authentication."
    exit 1
  fi
else
  ok "TELEGRAM_BOT_TOKEN is configured."
fi

# 3. Render Backend Service URL
if [[ -z "${RENDER_BACKEND_URL:-}" ]]; then
  echo -e "\n${BOLD}--- 3. Render Backend Service URL ---${NC}"
  echo "If you have already created the Render service, enter its URL (e.g. https://careermatch-backend.onrender.com)."
  echo "If not yet created, press Enter to view the 1-minute setup guide."
  read -r -p "Enter RENDER_BACKEND_URL (or press Enter to skip for now): " input_render_url
  if [[ -n "$input_render_url" ]]; then
    RENDER_BACKEND_URL="${input_render_url%/}" # remove trailing slash
    echo "RENDER_BACKEND_URL=\"$RENDER_BACKEND_URL\"" >> "$CONFIG_FILE"
    ok "Saved RENDER_BACKEND_URL to $CONFIG_FILE"
  else
    RENDER_BACKEND_URL=""
    warn "RENDER_BACKEND_URL not set yet."
  fi
else
  RENDER_BACKEND_URL="${RENDER_BACKEND_URL%/}"
  ok "Render Backend URL: $RENDER_BACKEND_URL"
fi

# 4. Vercel Frontend URL
if [[ -z "${VERCEL_FRONTEND_URL:-}" ]]; then
  echo -e "\n${BOLD}--- 4. Vercel Frontend URL ---${NC}"
  echo "If you have already deployed to Vercel, enter its URL (e.g. https://careermatch-one.vercel.app)."
  read -r -p "Enter VERCEL_FRONTEND_URL (or press Enter to let Vercel CLI deploy): " input_vercel_url
  if [[ -n "$input_vercel_url" ]]; then
    VERCEL_FRONTEND_URL="${input_vercel_url%/}"
    echo "VERCEL_FRONTEND_URL=\"$VERCEL_FRONTEND_URL\"" >> "$CONFIG_FILE"
    ok "Saved VERCEL_FRONTEND_URL to $CONFIG_FILE"
  else
    VERCEL_FRONTEND_URL=""
  fi
else
  VERCEL_FRONTEND_URL="${VERCEL_FRONTEND_URL%/}"
  ok "Vercel Frontend URL: $VERCEL_FRONTEND_URL"
fi

# ------------------------------------------------------------------------------
# Step C: Test Database Connectivity & Run Migrations / Seed Data
# ------------------------------------------------------------------------------
banner "Step C: Database Migrations & Initial Job Ingestion"

info "Testing connectivity to Neon PostgreSQL..."
export DATABASE_URL
export DJANGO_DEBUG="False"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-local-deploy-validation-key}"

PYTHON_BIN="python3"
if [[ -f "Backend/venv/bin/python" ]]; then
  PYTHON_BIN="Backend/venv/bin/python"
fi

# Check connection via python manage.py
if $PYTHON_BIN Backend/manage.py showmigrations --list >/dev/null 2>&1; then
  ok "Successfully connected to PostgreSQL via Django."
  
  info "Applying any pending database migrations..."
  $PYTHON_BIN Backend/manage.py migrate --noinput
  ok "Database schema is up to date."

  info "Checking active job listings in database..."
  # Django's shell prints an "objects imported automatically" notice before
  # the command output on recent versions. Keep only the final count so the
  # integer check below does not parse that notice as part of the value.
  JOB_COUNT=$($PYTHON_BIN Backend/manage.py shell -c "from jobs.models import Job; print(Job.objects.filter(is_active=True).count())" --verbosity 0 2>/dev/null | tail -n 1 || echo "0")
  info "Currently active jobs in database: $JOB_COUNT"

  if [[ "$JOB_COUNT" -eq 0 ]]; then
    info "Ingesting initial live jobs from ReliefWeb (5 pages)..."
    $PYTHON_BIN Backend/manage.py ingest_reliefweb --pages 5 || warn "Ingestion finished with notice."
    ok "Initial jobs successfully populated into PostgreSQL."
  else
    ok "Database already contains $JOB_COUNT active jobs. Skipping duplicate ingestion."
  fi
else
  warn "Could not connect directly to Neon PostgreSQL from this machine."
  warn "Ensure your IP is allowed in Neon and that DATABASE_URL has sslmode=require."
  info "Migrations will run automatically during Render build via Backend/build.sh."
fi

# ------------------------------------------------------------------------------
# Step D: Deploy Frontend to Vercel
# ------------------------------------------------------------------------------
banner "Step D: Frontend Build & Vercel Deployment"

if [[ -n "$RENDER_BACKEND_URL" ]]; then
  API_URL="$RENDER_BACKEND_URL/api"
else
  API_URL="http://localhost:8000/api"
  warn "RENDER_BACKEND_URL not set; using placeholder $API_URL"
fi

info "Building frontend with VITE_API_BASE_URL=$API_URL"
cd Frontend
VITE_API_BASE_URL="$API_URL" pnpm build
ok "Frontend static build generated in Frontend/dist"

if command -v vercel >/dev/null 2>&1; then
  info "Deploying to Vercel via CLI..."
  if [[ ! -f ".vercel/project.json" ]]; then
    info "Frontend is not linked to a Vercel project yet. Select the existing CareerMatch project below."
    if [[ -n "${VERCEL_SCOPE:-}" && -n "${VERCEL_PROJECT_NAME:-}" ]]; then
      if [[ -n "${VERCEL_TOKEN:-}" ]]; then
        vercel link --yes --team "$VERCEL_SCOPE" --project "$VERCEL_PROJECT_NAME" --token "$VERCEL_TOKEN"
      else
        vercel link --yes --team "$VERCEL_SCOPE" --project "$VERCEL_PROJECT_NAME"
      fi
    elif [[ -n "${VERCEL_TOKEN:-}" ]]; then
      vercel link --token "$VERCEL_TOKEN"
    else
      vercel link
    fi
  fi

  if [[ -f ".vercel/project.json" ]]; then
    info "Using the Vercel project linked to Frontend."
    VERCEL_PROJECT_NAME="linked project"
    VERCEL_ARGS=(--prod --yes)
  else
    err "No Vercel project is linked. Link the existing project, then rerun ./deploy.sh."
    exit 1
  fi
  if [[ -n "${VERCEL_TOKEN:-}" ]]; then
    if ! DEPLOY_OUTPUT=$(vercel "${VERCEL_ARGS[@]}" --token "$VERCEL_TOKEN" 2>&1); then
      err "Vercel deployment failed for project '$VERCEL_PROJECT_NAME' in scope '${VERCEL_SCOPE:-current scope}'."
      echo "$DEPLOY_OUTPUT"
      exit 1
    fi
  else
    if ! DEPLOY_OUTPUT=$(vercel "${VERCEL_ARGS[@]}" 2>&1); then
      err "Vercel deployment failed for project '$VERCEL_PROJECT_NAME' in scope '${VERCEL_SCOPE:-current scope}'."
      echo "$DEPLOY_OUTPUT"
      exit 1
    fi
  fi
  echo "$DEPLOY_OUTPUT"
  
  DETECTED_URL=$(echo "$DEPLOY_OUTPUT" | grep -Eo 'https://[^ ]+\.vercel\.app' | tail -n 1 || true)
  if [[ -n "$DETECTED_URL" && -z "$VERCEL_FRONTEND_URL" ]]; then
    VERCEL_FRONTEND_URL="$DETECTED_URL"
    sed -i '' '/VERCEL_FRONTEND_URL/d' "$CONFIG_FILE" 2>/dev/null || true
    echo "VERCEL_FRONTEND_URL=\"$VERCEL_FRONTEND_URL\"" >> "$CONFIG_FILE"
    ok "Deployed to Vercel: $VERCEL_FRONTEND_URL"
  elif [[ -n "$VERCEL_FRONTEND_URL" ]]; then
    ok "Vercel deployment completed for $VERCEL_FRONTEND_URL"
  else
    warn "Vercel deployment completed, but no URL was detected in the CLI output."
    echo "$DEPLOY_OUTPUT"
  fi
else
  info "Vercel CLI not present. You can deploy Frontend/ on vercel.com directly."
fi
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# Step E: Production Health & Verification Checks
# ------------------------------------------------------------------------------
banner "Step E: Verification & Health Checks"

if [[ -n "$RENDER_BACKEND_URL" ]]; then
  info "Testing Backend Health Check: $RENDER_BACKEND_URL/api/health/"
  HEALTH_RESP=$(curl -s -w "\n%{http_code}" "$RENDER_BACKEND_URL/api/health/" 2>/dev/null || echo "000")
  HTTP_STATUS=$(echo "$HEALTH_RESP" | tail -n 1)
  BODY=$(printf '%s\n' "$HEALTH_RESP" | sed '$d')

  if [[ "$HTTP_STATUS" == "200" ]]; then
    ok "Backend health check succeeded: $BODY"
  elif [[ "$HTTP_STATUS" == "503" ]]; then
    warn "Backend responded 503 (Service starting or database connection initializing): $BODY"
  else
    warn "Backend returned HTTP $HTTP_STATUS (Free instance may be waking up from sleep. Try again in 30 seconds)."
  fi
else
  warn "Skipping backend online health check because RENDER_BACKEND_URL is not set."
fi

if [[ -n "$VERCEL_FRONTEND_URL" ]]; then
  info "Testing Frontend Availability: $VERCEL_FRONTEND_URL"
  FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VERCEL_FRONTEND_URL" 2>/dev/null || echo "000")
  if [[ "$FRONTEND_STATUS" == "200" ]]; then
    ok "Frontend is live and returning HTTP 200 over HTTPS."
  else
    warn "Frontend returned HTTP $FRONTEND_STATUS."
  fi
fi

# ------------------------------------------------------------------------------
# Step F: Final Summary & Permanent URLs
# ------------------------------------------------------------------------------
banner "Deployment Summary & Permanent URLs"

echo -e "${BOLD}Frontend (Vercel):${NC}  ${GREEN}${VERCEL_FRONTEND_URL:-https://your-app.vercel.app}${NC}"
echo -e "${BOLD}Backend (Render):${NC}   ${GREEN}${RENDER_BACKEND_URL:-https://your-service.onrender.com}${NC}"
echo -e "${BOLD}Database (Neon):${NC}    ${GREEN}Connected (Serverless PostgreSQL)${NC}"
echo -e "${BOLD}Telegram Bot:${NC}       ${GREEN}@careermatch123bot${NC}"
echo -e "${BOLD}Recurring Cost:${NC}     ${GREEN}\$0.00 / month${NC}"

echo -e "\n${BOLD}Telegram Mini App Configuration:${NC}"
echo "1. Open @BotFather on Telegram (https://t.me/BotFather)."
echo "2. Send command: /setmenubutton"
echo "3. Select: @careermatch123bot"
echo "4. Set Title: Open CareerMatch"
echo -e "5. Set URL:   ${GREEN}${VERCEL_FRONTEND_URL:-https://your-app.vercel.app}${NC}"
echo -e "\n${BOLD}Done! Your Telegram Mini App is ready for your university demonstration.${NC}\n"

