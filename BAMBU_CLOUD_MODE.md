# BAMBU_CLOUD_MODE.md

Goal: Keep printer in cloud mode (phone app works) while enabling controlled automation.

## Findings
- Local MQTT status/control works (light on/off, status polling).
- Local raw print start (`project_file`) is blocked in current cloud mode (`err_code 84033543`).
- No reliable/supported remote MQTT command found to toggle LAN Only mode.
- Third-party print start generally requires Bambu authorization path (Bambu Connect / Studio auth flow).

## Installed tool
- `bambu-cli` (npm package) installed globally.
- Probe wrapper: `tools/bambu_cloud_probe.sh`

## Runbook
### 1) Interactive login (required once)
Run in a real terminal (TTY):
```bash
bash tools/bambu_cloud_probe.sh login
```
This prompts for Bambu account credentials and verification.

### 2) Verify cloud machine list
```bash
bash tools/bambu_cloud_probe.sh
```

### 3) Next commands after login
```bash
bambu-cli machines
bambu-cli status --id <machine_id> --json
bambu-cli files --id <machine_id>
```

## Planned next build
- Add `tools/bambu_cloud_print.py` wrapper to:
  1) pick file
  2) upload via bambu-cli
  3) start print via authorized path
  4) monitor status with `tools/bambu_status.py`

## Safety
- Keep explicit EXECUTE gate for physical actions (print start/cancel).
