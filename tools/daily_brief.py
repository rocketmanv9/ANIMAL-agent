#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime

EMAIL_BRIEF = '/home/grant/.openclaw/workspace/tools/email_brief.py'
WEATHER_OPS = '/home/grant/.openclaw/workspace/tools/weather_ops.py'


def run_json(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return json.loads(p.stdout)


def main():
    email = run_json(['python3', EMAIL_BRIEF, '--max', '25', '--json'])
    weather = run_json(['python3', WEATHER_OPS, 'Vancouver WA', '--json'])

    print(f"Daily Brief — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print('')
    print('Email triage:')
    print(f"- Read now: {len(email['read_now'])}")
    print(f"- Check soon: {len(email['check_soon'])}")
    print(f"- Skip/batch: {len(email['skip_or_batch'])}")

    top = email['read_now'][:3] if email['read_now'] else email['check_soon'][:3]
    if top:
        print('- Top items:')
        for t in top:
            print(f"  - {t['subject']} — {t['from']}")

    print('')
    print('Weather (Vancouver WA):')
    print(f"- {weather['time']}: {weather['condition']}, {weather['temp_c']}°C (feels {weather['feels_c']}°C), rain {weather['rain_chance_pct']}%")


if __name__ == '__main__':
    main()
