# WEATHER_OPS.md

Fast city/address weather lookup (no API key) using wttr.in.

## Script
- `tools/weather_ops.py`

## Usage
```bash
# Current + today summary
python3 tools/weather_ops.py "Seattle"

# Current + tomorrow summary
python3 tools/weather_ops.py "Vancouver, WA" --tomorrow

# JSON output
python3 tools/weather_ops.py "Portland" --json
```

## Notes
- Works with city names and most addresses.
- Uses short cache (10 min) at `.openclaw/weather_cache.json` for speed.
- Source: wttr.in (`?format=j1`)
