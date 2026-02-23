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

## Status polling (implemented)
Read-only MQTT status script:

```bash
python3 tools/bambu_status.py --ip 192.168.0.111 --serial 01P00C5B0403147 --access-code <ACCESS_CODE> --json
```

Recent test result:
- connected: true
- status_received: true
- gcode_state: FINISH
- mc_percent: 100
- nozzle_temper: ~42.2°C
- bed_temper: ~40.4°C
- wifi_signal: -36dBm

## Next build steps (safe)
1. Add printer profile JSON (`tools/bambu_profile.json`) with IP + access code + serial placeholder.
2. Add "preflight" script that refuses to run if printer is currently printing.
3. Add optional slice-export automation via Bambu Studio CLI.
4. Add guarded print-submit flow (explicit EXECUTE required).
