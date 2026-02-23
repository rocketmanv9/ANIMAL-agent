#!/usr/bin/env bash
set -euo pipefail

if ! command -v bambu-cli >/dev/null 2>&1; then
  echo "ERROR: bambu-cli not installed"
  exit 1
fi

echo "== bambu-cli version =="
bambu-cli --version || true

echo
if [[ "${1:-}" == "login" ]]; then
  echo "== interactive login =="
  echo "This requires TTY prompts for bambulab.com credentials + verification code."
  bambu-cli login
  exit 0
fi

echo "== machines (requires prior login cache) =="
if bambu-cli machines --json >/tmp/bambu_cloud_machines.json 2>/tmp/bambu_cloud_err.log; then
  cat /tmp/bambu_cloud_machines.json
else
  echo "NOT_LOGGED_IN"
  cat /tmp/bambu_cloud_err.log
  exit 2
fi
