#!/usr/bin/env bash
set -euo pipefail
cd /home/grant/.openclaw/workspace

# Resurface incomplete work + infra blockers
python3 tools/persistctl.py resurface

# Optional: record an operational step heartbeat
python3 tools/persistctl.py step --summary "scheduler resurfaced tasks" --payload '{"source":"persistence_scheduler"}'
