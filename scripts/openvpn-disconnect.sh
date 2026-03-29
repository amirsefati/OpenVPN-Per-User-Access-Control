#!/usr/bin/env bash
set -euo pipefail

curl -sS -X POST "http://127.0.0.1:8000/internal/vpn-event/disconnect" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: ${INTERNAL_API_KEY:-change-internal-key}" \
  -d "{
    \"common_name\": \"${common_name:-}\",
    \"bytes_received\": ${bytes_received:-0},
    \"bytes_sent\": ${bytes_sent:-0}
  }" >/dev/null

