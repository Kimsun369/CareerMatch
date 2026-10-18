#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -euo pipefail

echo "==> Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Build completed successfully."

