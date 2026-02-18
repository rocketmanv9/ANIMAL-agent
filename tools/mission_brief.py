#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta

GOG = '/mnt/c/Users/grant/bin/gogcli/gog.exe'
GCAL = '/mnt/c/Users/grant/AppData/Roaming/Python/Python312/Scripts/gcalcli.exe'
ACCOUNT = 'grant.m.anderson2021@gmail.com'


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout


def get_email_triage(max_items=20):
    out = run(['python3', '/home/grant/.openclaw/workspace/tools/email_brief.py', '--max', str(max_items), '--json'])
    return json.loads(out)


def get_calendar_window(days=3):
    start = datetime.now().strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    out = run([GCAL, '--nocolor', '--calendar', ACCOUNT, 'agenda', start, end])
    return out


def parse_agenda_lines(text):
    events = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        # Example: Tue Mar 17           House Closing Date
        # Example: Fri Feb 20  1:00pm   Home inspection
        m = re.match(r'^([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2})(?:\s+(\d{1,2}:\d{2}(?:am|pm)))?\s+(.*)$', l)
        if m:
            day, tm, title = m.groups()
            events.append({'day': day, 'time': tm or 'ALL DAY', 'title': title.strip()})
    return events


def focus_flags(events):
    flags = []
    keywords = ['inspection', 'closing', 'deadline', 'meeting', 'payment', 'tax', 'renewal']
    for e in events:
        low = e['title'].lower()
        if any(k in low for k in keywords):
            flags.append(e)
    return flags


def main():
    ap = argparse.ArgumentParser(description='Daily mission briefing (calendar + email triage)')
    ap.add_argument('--days', type=int, default=3, help='Calendar lookahead days')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    triage = get_email_triage(max_items=25)
    cal_raw = get_calendar_window(days=args.days)
    events = parse_agenda_lines(cal_raw)
    critical = focus_flags(events)

    result = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'calendar': {
            'lookahead_days': args.days,
            'total_events': len(events),
            'events': events,
            'focus_events': critical,
        },
        'email': {
            'read_now': len(triage.get('read_now', [])),
            'check_soon': len(triage.get('check_soon', [])),
            'skip_or_batch': len(triage.get('skip_or_batch', [])),
            'top_read_now': triage.get('read_now', [])[:5],
        }
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Mission Brief — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print('\nCalendar (next {} days):'.format(args.days))
    if not events:
        print('- No events found.')
    else:
        for e in events[:12]:
            print(f"- {e['day']} {e['time']} — {e['title']}")

    print('\nFocus now (calendar):')
    if not critical:
        print('- No critical keyword events detected.')
    else:
        for e in critical[:8]:
            print(f"- {e['day']} {e['time']} — {e['title']}")

    print('\nEmail triage:')
    print(f"- Read now: {result['email']['read_now']}")
    print(f"- Check soon: {result['email']['check_soon']}")
    print(f"- Skip/batch: {result['email']['skip_or_batch']}")

    top = result['email']['top_read_now']
    if top:
        print('- Top read-now threads:')
        for t in top:
            print(f"  - {t['subject']} — {t['from']}")


if __name__ == '__main__':
    main()
