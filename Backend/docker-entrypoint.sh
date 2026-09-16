#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
python - <<'PY'
import os, time, sys
import dj_database_url
import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    sys.exit(0)

cfg = dj_database_url.parse(url)
for attempt in range(30):
    try:
        psycopg2.connect(
            dbname=cfg["NAME"], user=cfg["USER"], password=cfg["PASSWORD"],
            host=cfg["HOST"], port=cfg["PORT"],
        ).close()
        print("PostgreSQL is up.")
        break
    except Exception as exc:
        print(f"  not ready yet ({exc}); retrying...")
        time.sleep(1)
else:
    print("PostgreSQL never became ready.", file=sys.stderr)
    sys.exit(1)
PY

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Starting Django dev server..."
exec python manage.py runserver 0.0.0.0:8000
