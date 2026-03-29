#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
TOKEN="${TOKEN:?Set TOKEN env var with admin JWT}"
USERNAME="${1:?Usage: remove_domain.sh <username> <domain>}"
DOMAIN="${2:?Usage: remove_domain.sh <username> <domain>}"

JSON="$(curl -sS "$API_URL/users" -H "Authorization: Bearer $TOKEN")"
USER_ID="$(python3 -c "import json,sys; data=json.load(sys.stdin); print(next((str(u['id']) for u in data if u['username']=='$USERNAME'), ''))" <<< "$JSON")"
[ -n "$USER_ID" ] || { echo "User not found"; exit 1; }

DOMAINS="$(curl -sS "$API_URL/users/$USER_ID/domains" -H "Authorization: Bearer $TOKEN")"
DOMAIN_ID="$(python3 -c "import json,sys; data=json.load(sys.stdin); print(next((str(d['id']) for d in data if d['domain']=='$DOMAIN'), ''))" <<< "$DOMAINS")"
[ -n "$DOMAIN_ID" ] || { echo "Domain not found"; exit 1; }

curl -sS -X DELETE "$API_URL/users/$USER_ID/domains/$DOMAIN_ID" \
  -H "Authorization: Bearer $TOKEN"
echo

