# EMAIL_OPS.md

Fast Gmail triage helper.

## Script
- `tools/email_brief.py`

## What it does
- Pulls recent threads from Gmail via `gog`
- Scores each thread for priority
- Buckets into:
  - `read_now`
  - `check_soon`
  - `skip_or_batch`

## Usage
```bash
# Default: newer_than:1d, max 30
python3 tools/email_brief.py

# Custom query
python3 tools/email_brief.py --query "newer_than:2d in:inbox" --max 50

# JSON output
python3 tools/email_brief.py --json
```

## Notes
- Uses your connected Gmail account (`grant.m.anderson2021@gmail.com` by default).
- Can be pointed at another account with `--account` once OAuth is connected.
