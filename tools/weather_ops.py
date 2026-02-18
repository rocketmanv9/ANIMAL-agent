#!/usr/bin/env python3
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_PATH = Path('/home/grant/.openclaw/workspace/.openclaw/weather_cache.json')
TTL = 600  # 10 min


def load_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {}


def save_cache(c):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(c, indent=2))


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "ANIMAL-weather/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode('utf-8', errors='replace'))


def get_forecast(location: str):
    loc = location.strip()
    key = f"forecast:{loc.lower()}"
    cache = load_cache()
    now = time.time()
    if key in cache and now - cache[key].get('ts', 0) < TTL:
        return cache[key]['data'], True

    q = urllib.parse.quote(loc.replace(' ', '+'))
    url = f"https://wttr.in/{q}?format=j1"
    data = fetch_json(url)
    cache[key] = {"ts": now, "data": data}
    save_cache(cache)
    return data, False


def summarize_current(data, location):
    cur = (data.get('current_condition') or [{}])[0]
    w = (cur.get('weatherDesc') or [{"value": "Unknown"}])[0].get('value', 'Unknown')
    return {
        "location": location,
        "condition": w,
        "temp_c": cur.get('temp_C'),
        "feelslike_c": cur.get('FeelsLikeC'),
        "humidity_pct": cur.get('humidity'),
        "wind_kmph": cur.get('windspeedKmph'),
        "wind_dir": cur.get('winddir16Point'),
    }


def summarize_day(data, day_index=0):
    days = data.get('weather') or []
    if day_index >= len(days):
        return None
    d = days[day_index]
    astro = (d.get('astronomy') or [{}])[0]
    hourly = d.get('hourly') or []
    rain_max = 0
    for h in hourly:
        try:
            rain_max = max(rain_max, int(h.get('chanceofrain', '0') or 0))
        except Exception:
            pass
    return {
        "date": d.get('date'),
        "max_c": d.get('maxtempC'),
        "min_c": d.get('mintempC'),
        "avg_c": d.get('avgtempC'),
        "sunrise": astro.get('sunrise'),
        "sunset": astro.get('sunset'),
        "max_rain_chance_pct": rain_max,
    }


def main():
    ap = argparse.ArgumentParser(description='Fast weather lookup via wttr.in (no API key)')
    ap.add_argument('location', help='City, address, or place')
    ap.add_argument('--tomorrow', action='store_true', help='Return tomorrow summary')
    ap.add_argument('--json', action='store_true', help='JSON output')
    args = ap.parse_args()

    data, cached = get_forecast(args.location)
    out = {
        "ok": True,
        "source": "wttr.in",
        "cached": cached,
        "current": summarize_current(data, args.location),
    }
    if args.tomorrow:
        out["tomorrow"] = summarize_day(data, day_index=1)
    else:
        out["today"] = summarize_day(data, day_index=0)

    if args.json:
        print(json.dumps(out, indent=2))
        return

    c = out['current']
    print(f"{c['location']}: {c['condition']}, {c['temp_c']}°C (feels {c['feelslike_c']}°C), humidity {c['humidity_pct']}%, wind {c['wind_dir']} {c['wind_kmph']} km/h")
    d = out['tomorrow'] if args.tomorrow else out['today']
    if d:
        label = 'Tomorrow' if args.tomorrow else 'Today'
        print(f"{label} ({d['date']}): {d['min_c']}–{d['max_c']}°C, rain chance up to {d['max_rain_chance_pct']}%, sunrise {d['sunrise']}, sunset {d['sunset']}")


if __name__ == '__main__':
    main()
