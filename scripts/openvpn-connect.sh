#!/usr/bin/env bash
set -euo pipefail

curl -sS -X POST "http://127.0.0.1:8000/internal/vpn-event/connect" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: ${INTERNAL_API_KEY:-change-internal-key}" \
  -d "{
    \"common_name\": \"${common_name:-}\",
    \"real_ip\": \"${trusted_ip:-}\",
    \"vpn_ip\": \"${ifconfig_pool_remote_ip:-}\"
  }" >/dev/null

