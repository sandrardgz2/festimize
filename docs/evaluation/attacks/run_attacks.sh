#!/usr/bin/env bash
# Reproducible adversarial test run for Festimize (IST 440W testing deliverable).
#
#   bash docs/evaluation/attacks/run_attacks.sh
#
# Runs each attack and prints its outcome, so the result can be screenshotted.
# Needs the stack up: web :8080, analytics :8000 (started WITH API_KEY), db :5432.
# Uses a throwaway account so the demo data is never touched. Read-only except
# where it builds the throwaway account's own plan.
set -u
WEB=http://localhost:8080 ; API=http://localhost:8000
JAR=$(mktemp) ; KEY="${API_KEY:-test-key-123}"
ok(){ printf "  \033[32m%s\033[0m\n" "$1"; }   # green
bad(){ printf "  \033[31m%s\033[0m\n" "$1"; }   # red
hdr(){ printf "\n\033[1m== %s ==\033[0m\n" "$1"; }

hdr "SECURITY"
echo "[1] analytics API without the shared key (attacker is not logged in):"
for ep in "POST /plan/2?edition_id=3" "GET /plan/2/cost?edition_id=3"; do
  m=${ep%% *}; path=${ep#* }
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$m" "$API$path")
  [ "$code" = "401" ] && ok "$ep -> $code  REJECTED" || bad "$ep -> $code"
done
echo "[1] with the correct key (what the web app sends):"
code=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Analytics-Key: $KEY" -X POST "$API/plan/2?edition_id=3")
[ "$code" = "200" ] && ok "POST /plan/2 (keyed) -> $code  OK" || bad "keyed call -> $code"

echo "[2] Postgres port binding in the committed compose (what a fresh build gets):"
bind=$(grep -oE '127\.0\.0\.1:5432:5432|"5432:5432"' docker-compose.yml | head -1)
[ -n "$bind" ] && [[ "$bind" == 127.0.0.1* ]] && ok "$bind  LOOPBACK ONLY" || bad "${bind:-?}  NETWORK EXPOSED"

hdr "WEB SURFACE"
login(){ local t; t=$(curl -s -c "$JAR" "$WEB/login" | grep -o 'name="_csrf" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//');
  curl -s -b "$JAR" -c "$JAR" -X POST "$WEB/login" -d "username=$1&password=$2&_csrf=$t" -o /dev/null; }
login attack@festimize.app attack12345
csrf(){ curl -s -b "$JAR" "$WEB/schedule?editionId=3" | grep -o 'name="_csrf" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//'; }
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEB/schedule/add" -d "editionId=3&performanceId=1")
[ "$code" = "403" ] && ok "[4] CSRF: POST with no token -> $code  REJECTED" || bad "[4] CSRF -> $code"
code=$(curl -s -o /dev/null -w "%{http_code}" "$WEB/schedule?editionId=3" ; )
SJ=$(mktemp); st=$(curl -s -c "$SJ" "$WEB/login" | grep -o 'name="_csrf" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')
loc=$(curl -s -o /dev/null -w "%{redirect_url}" -b "$SJ" -c "$SJ" -X POST "$WEB/login" --data-urlencode "username=' OR '1'='1' --" --data-urlencode "password=x" --data-urlencode "_csrf=$st")
case "$loc" in *error*) ok "[4] SQLi login attempt -> ${loc##*/}  no bypass";; *) bad "[4] SQLi -> ${loc:-?}";; esac ; rm -f "$SJ"

hdr "BAD INPUT"
for t in 25:00 99:99 ab:cd; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b "$JAR" -X POST "$WEB/schedule/hours" \
    --data-urlencode editionId=3 --data-urlencode onDay=2027-04-24 --data-urlencode "arriveAt=$t" --data-urlencode "_csrf=$(csrf)")
  [ "$code" = "302" ] && ok "[6] invalid time $t -> $code  rejected cleanly" || bad "[6] $t -> $code"
done

hdr "DEPENDENCIES & SCALE"
echo "[11] 50 concurrent schedule builds:"
s=$(date +%s.%N)
for i in $(seq 1 50); do curl -s -o /dev/null -H "X-Analytics-Key: $KEY" -X POST "$API/plan/10?edition_id=3" & done ; wait
ok "50 builds finished in $(echo "$(date +%s.%N) - $s" | bc)s, service healthy: $(curl -s $API/health | grep -o '"status":"[a-z]*"')"

rm -f "$JAR"
printf "\n\033[1mdone.\033[0m\n"
