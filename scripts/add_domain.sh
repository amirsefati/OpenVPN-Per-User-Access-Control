#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
TOKEN="${TOKEN:?Set TOKEN env var with admin JWT}"
USERNAME="${1:?Usage: add_domain.sh <username> <domain>}"
DOMAIN="${2:?Usage: add_domain.sh <username> <domain>}"

USER_ID="$(curl -sS "$API_URL/users" -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; data=json.load(sys.stdin); print(next((str(u['id']) for u in data if u['username']=='$USERNAME'), ''))")"
[ -n "$USER_ID" ] || { echo "User not found"; exit 1; }

curl -sS -X POST "$API_URL/users/$USER_ID/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"domain\":\"$DOMAIN\"}"
echo

