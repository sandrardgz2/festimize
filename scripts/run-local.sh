#!/usr/bin/env bash
# Start Festimize locally with the analytics API locked, the way it runs in
# deployment. One command, so the running stack matches the committed config
# and every security fix is active — not just bound to localhost.
#
#   bash scripts/run-local.sh
#
# Needs the database up first:  docker compose up -d db
set -euo pipefail
cd "$(dirname "$0")/.."

# A shared secret the web app presents to the analytics API. Local-only, so a
# fixed value is fine; override by exporting ANALYTICS_KEY before running.
KEY="${ANALYTICS_KEY:-festimize-local-$(id -u)}"
DB="postgresql+psycopg://festimize:festimize@localhost:5432/festimize"
LOG="${TMPDIR:-/tmp}/festimize"
mkdir -p "$LOG"

echo "Stopping any previous run..."
pkill -f "uvicorn app.main" 2>/dev/null || true
pkill -f "spring-boot:run" 2>/dev/null || true
sleep 3

echo "Starting analytics (:8000, key-protected)..."
( cd analytics && DATABASE_URL="$DB" API_KEY="$KEY" \
    nohup .venv/bin/python -m uvicorn app.main:app --port 8000 > "$LOG/analytics.log" 2>&1 & )
sleep 5

echo "Starting web app (:8080, sends the key)..."
( cd app && FESTIMIZE_ANALYTICS_KEY="$KEY" \
    nohup ./mvnw -o spring-boot:run > "$LOG/web.log" 2>&1 & )

printf "Waiting for the web app"
for _ in $(seq 1 60); do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/login 2>/dev/null)" = "200" ]; then
    echo " — up."
    echo "Festimize is running at http://localhost:8080"
    echo "Logs: $LOG"
    exit 0
  fi
  printf "."; sleep 3
done
echo " — did not come up; see $LOG/web.log"
exit 1
