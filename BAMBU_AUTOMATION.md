# BAMBU_AUTOMATION.md

## Current target
- Printer IP: `192.168.0.111`
- Mode: LAN only capable

## Safety policy
- If printer is actively printing, run read-only checks only.
- No print start/stop/cancel commands without explicit approval.

## Read-only readiness test
```bash
python3 tools/bambu_probe.py --ip 192.168.0.111 --json
```

## What "ready" means in probe
- Host can reach printer IP (ping)
- Bambu Studio installed and CLI help works
- Core LAN ports open on printer (8883, 990)

## Next build steps (safe)
1. Add printer profile JSON (`tools/bambu_profile.json`) with IP + access code + serial placeholder.
2. Add status-poll script (MQTT read-only) for printer state.
3. Add "preflight" script that refuses to run if printer is currently printing.
4. Add optional slice-export automation via Bambu Studio CLI.
