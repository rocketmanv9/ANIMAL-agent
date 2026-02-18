# WEATHER_OPS.md

Fast weather lookup for city/address/hour.

## Script
- `tools/weather_ops.py`
- Source: Open-Meteo (free, no API key)
- Caching:
  - forecast cache: 10 min
  - geocode cache: 30 days

## Usage
```bash
# Current-ish weather
python3 tools/weather_ops.py "Seattle"

# Specific time
python3 tools/weather_ops.py "Vancouver, WA" --at "2026-02-20T08:00"

# JSON
python3 tools/weather_ops.py "Portland" --at "2026-02-20T08:00" --json
```

## Fast aliases
Built-in direct coordinate aliases for:
- Vancouver / Vancouver WA / Vancouver Washington
- Seattle
- Portland

This avoids geocoding round-trips for common requests.
