#!/usr/bin/env python3
import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

CACHE_PATH = Path('/home/grant/.openclaw/workspace/.openclaw/weather_cache.json')
GEO_CACHE_PATH = Path('/home/grant/.openclaw/workspace/.openclaw/weather_geo_cache.json')
TTL = 600  # 10 min forecast cache
GEO_TTL = 86400 * 30  # 30 days geocode cache

# Fast path aliases for common requests (can expand over time)
ALIASES = {
    'vancouver': (45.6387, -122.6615, 'Vancouver, WA'),
    'vancouver wa': (45.6387, -122.6615, 'Vancouver, WA'),
    'vancouver washington': (45.6387, -122.6615, 'Vancouver, WA'),
    'seattle': (47.6062, -122.3321, 'Seattle, WA'),
    'portland': (45.5152, -122.6784, 'Portland, OR'),
}


def _load(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "ANIMAL-weather/2.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode('utf-8', errors='replace'))


def geocode(location: str):
    key = location.strip().lower()

    if key in ALIASES:
        lat, lon, label = ALIASES[key]
        return lat, lon, label, True

    cache = _load(GEO_CACHE_PATH)
    hit = cache.get(key)
    if hit and time.time() - hit.get('ts', 0) < GEO_TTL:
        return hit['lat'], hit['lon'], hit.get('label', location), True

    # Open-Meteo geocoding (fast, free)
    geo_url = (
        'https://geocoding-api.open-meteo.com/v1/search?name=' +
        urllib.parse.quote(location) +
        '&count=1&language=en&format=json'
    )
    data = fetch_json(geo_url)
    results = data.get('results') or []
    if not results:
        raise RuntimeError(f'Could not geocode location: {location}')

    r = results[0]
    lat, lon = r['latitude'], r['longitude']
    label = ', '.join([x for x in [r.get('name'), r.get('admin1'), r.get('country')] if x])

    cache[key] = {'lat': lat, 'lon': lon, 'label': label, 'ts': time.time()}
    _save(GEO_CACHE_PATH, cache)
    return lat, lon, label, False


def forecast(lat, lon, timezone='America/Los_Angeles'):
    key = f"fc:{lat:.4f},{lon:.4f}:{timezone}"
    cache = _load(CACHE_PATH)
    hit = cache.get(key)
    if hit and time.time() - hit.get('ts', 0) < TTL:
        return hit['data'], True

    url = (
        f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
        '&hourly=temperature_2m,apparent_temperature,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m'
        '&temperature_unit=celsius&wind_speed_unit=kmh'
        f'&timezone={urllib.parse.quote(timezone)}&forecast_days=7'
    )
    data = fetch_json(url)
    cache[key] = {'ts': time.time(), 'data': data}
    _save(CACHE_PATH, cache)
    return data, False


def weather_code_desc(code: int):
    mapping = {
        0: 'Clear', 1: 'Mostly clear', 2: 'Partly cloudy', 3: 'Overcast',
        45: 'Fog', 48: 'Rime fog',
        51: 'Light drizzle', 53: 'Drizzle', 55: 'Dense drizzle',
        61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
        71: 'Light snow', 73: 'Snow', 75: 'Heavy snow',
        80: 'Rain showers', 81: 'Rain showers', 82: 'Violent rain showers',
        95: 'Thunderstorm',
    }
    return mapping.get(code, f'Weather code {code}')


def nearest_hour_index(times, target_iso):
    target = datetime.fromisoformat(target_iso)
    best_i, best_diff = 0, 10**18
    for i, t in enumerate(times):
        dt = datetime.fromisoformat(t)
        diff = abs((dt - target).total_seconds())
        if diff < best_diff:
            best_i, best_diff = i, diff
    return best_i


def main():
    ap = argparse.ArgumentParser(description='Fast weather lookup (city/address/hour)')
    ap.add_argument('location', help='City or address')
    ap.add_argument('--at', help='Local time: YYYY-MM-DDTHH:MM (e.g., 2026-02-20T08:00)')
    ap.add_argument('--timezone', default='America/Los_Angeles')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    lat, lon, label, geo_cached = geocode(args.location)
    data, fc_cached = forecast(lat, lon, args.timezone)

    times = data['hourly']['time']
    if args.at:
        idx = nearest_hour_index(times, args.at)
    else:
        # nearest to now in local tz by string compare fallback
        now_local = datetime.now().strftime('%Y-%m-%dT%H:00')
        idx = nearest_hour_index(times, now_local)

    out = {
        'ok': True,
        'location': label,
        'lat': lat,
        'lon': lon,
        'time': times[idx],
        'condition': weather_code_desc(int(data['hourly']['weather_code'][idx])),
        'temp_c': data['hourly']['temperature_2m'][idx],
        'feels_c': data['hourly']['apparent_temperature'][idx],
        'rain_chance_pct': data['hourly']['precipitation_probability'][idx],
        'wind_kmh': data['hourly']['wind_speed_10m'][idx],
        'wind_dir_deg': data['hourly']['wind_direction_10m'][idx],
        'geo_cached': geo_cached,
        'forecast_cached': fc_cached,
        'source': 'open-meteo'
    }

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(
            f"{out['location']} @ {out['time']}: {out['condition']}, "
            f"{out['temp_c']}°C (feels {out['feels_c']}°C), "
            f"rain {out['rain_chance_pct']}%, wind {out['wind_kmh']} km/h"
        )


if __name__ == '__main__':
    main()
