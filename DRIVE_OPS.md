# DRIVE_OPS.md

Fast CRUD wrapper for Google Drive via `gog`.

## Script
- Path: `tools/drive_ops.py`
- Default account: `grant.m.anderson2021@gmail.com`
- Default gog binary: `/mnt/c/Users/grant/bin/gogcli/gog.exe`

## Why this exists
- Fewer repetitive tool calls
- Short-lived ID cache for folder lookups
- JSON outputs for reliable automation

## Commands
```bash
# List root items (fast)
python3 tools/drive_ops.py ls --max 20

# Create folder at root (idempotent)
python3 tools/drive_ops.py mkdir "ANIMAL"

# Create doc in a named folder under root
python3 tools/drive_ops.py doc "ANIMAL TEST 2" --parent-name "ANIMAL" --file /tmp/test.md --markdown

# Move file to folder
python3 tools/drive_ops.py move <FILE_ID> <FOLDER_ID>

# Trash a file/folder
python3 tools/drive_ops.py delete <FILE_ID>
```

## Environment overrides
- `GOG_BIN` — path to gog executable
- `GOG_ACCOUNT` — target Google account
- `DRIVE_OPS_CACHE` — cache file path
- `DRIVE_OPS_CACHE_TTL` — cache TTL seconds (default 900)

## Cache
- File: `.openclaw/drive_id_cache.json`
- Key format: `folder:<parentId>:<name>`
- TTL default: 15 minutes

## Notes
- Delete uses trash by default.
- Permanent delete requires `--permanent`.
- Wrapper auto-applies force for non-interactive delete prompts.
