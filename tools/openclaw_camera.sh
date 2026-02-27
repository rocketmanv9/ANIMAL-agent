#!/usr/bin/env bash
# Wrapper to mimic: openclaw camera <subcommand>
set -euo pipefail
cd /home/grant/.openclaw/workspace
python3 -m camera.cli "$@"
