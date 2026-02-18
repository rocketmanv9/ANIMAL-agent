# MISSION_BRIEF.md

Daily mission briefing flow.

## Script
- `tools/mission_brief.py`

## What it includes
1) Calendar lookahead (default next 3 days)
2) Focus event extraction (keywords like closing/inspection/deadline)
3) Email triage summary (`read_now`, `check_soon`, `skip_or_batch`)

## Usage
```bash
python3 tools/mission_brief.py
python3 tools/mission_brief.py --days 5
python3 tools/mission_brief.py --json
```

## Intent
Use this as your morning command-brief so you know:
- what's scheduled
- what needs prep/focus
- what inbox items deserve immediate attention
