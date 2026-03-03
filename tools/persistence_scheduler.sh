#!/usr/bin/env bash
set -euo pipefail
cd /home/grant/.openclaw/workspace

# 1) Resurface incomplete work
python3 tools/persistctl.py resurface

# 2) Every run, reevaluate open loops (stale threshold defaults to 6h)
python3 tools/persistctl.py reevaluate --stale-hours 6 > /tmp/open_loops_reeval.json
cat /tmp/open_loops_reeval.json

# 3) Commit scheduler heartbeat
python3 tools/persistctl.py step --summary "scheduler resurfaced + reevaluated open loops" --payload '{"source":"persistence_scheduler"}'
