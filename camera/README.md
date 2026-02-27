# Camera Module (Local-Only)

This module adds local camera utilities:
- list devices
- capture still image
- record short clip
- best-effort "who is using camera"

## Privacy
First camera use requires consent. Grant once:

```bash
python3 -m camera.cli consent --grant
```

Consent is stored at:
- `camera/config.json`

## Commands

```bash
python3 -m camera.cli env
python3 -m camera.cli list
python3 -m camera.cli snap --out ./camera/test.jpg
python3 -m camera.cli clip --out ./camera/test.mp4 --seconds 5
python3 -m camera.cli who
```

Optional wrapper (mimics `openclaw camera ...`):

```bash
bash tools/openclaw_camera.sh env
bash tools/openclaw_camera.sh list
```

## WSL2 Note
In WSL2, direct webcam access is usually unavailable (`/dev/video*` missing).
Use host capture (Windows/macOS/Linux host terminal) instead.

### Host Windows test snap (laptop camera)
After installing FFmpeg on Windows and adding it to PATH:

```powershell
ffmpeg -list_devices true -f dshow -i dummy
ffmpeg -y -f dshow -i video="Integrated Camera" -frames:v 1 C:\claw_print\camera_test.jpg
```

## Troubleshooting
- Install ffmpeg if missing.
- Linux: install `v4l-utils` for better device metadata.
- If `snap`/`clip` fails, run `env` and `list` first.

## Acceptance test checklist
1. `python3 -m camera.cli env` returns OS/backend info.
2. `python3 -m camera.cli list` returns device info or clear WSL note.
3. `python3 -m camera.cli consent --grant` persists flag.
4. `python3 -m camera.cli snap --out ./camera/test.jpg` succeeds on host OS with camera.
5. `python3 -m camera.cli who` returns best-effort process data.
