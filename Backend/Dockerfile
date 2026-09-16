FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary needs libpq at runtime; build-essential + libpq-dev cover
# building it and any future C-extension deps cleanly.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
