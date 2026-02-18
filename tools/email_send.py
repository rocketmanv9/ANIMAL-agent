#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

GOG = "/mnt/c/Users/grant/bin/gogcli/gog.exe"
POLICY_PATH = Path('/home/grant/.openclaw/workspace/tools/email_policy.json')


def load_policy():
    if not POLICY_PATH.exists():
        raise RuntimeError(f'Missing policy file: {POLICY_PATH}')
    return json.loads(POLICY_PATH.read_text())


def infer_subject(body: str) -> str:
    text = ' '.join(body.strip().split())
    if not text:
        return 'Quick update'
    words = text.split(' ')
    subject = ' '.join(words[:8])
    if len(subject) > 72:
        subject = subject[:69].rstrip() + '...'
    return subject[0].upper() + subject[1:] if subject else 'Quick update'


def resolve_account(policy, sender):
    if not sender:
        return policy.get('defaultAccount')
    s = sender.strip().lower()
    if s in ('personal', 'grant.m.anderson2021@gmail.com'):
        return policy['accounts']['personal']
    if s in ('work', 'grant@acmoate.com'):
        return policy['accounts']['work']
    return sender


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout


def main():
    ap = argparse.ArgumentParser(description='Policy-aware Gmail sender')
    ap.add_argument('--to', required=True)
    ap.add_argument('--body', required=True)
    ap.add_argument('--subject')
    ap.add_argument('--sender', help='personal|work|email')
    ap.add_argument('--no-footer', action='store_true')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    policy = load_policy()
    account = resolve_account(policy, args.sender)
    subject = args.subject if args.subject else infer_subject(args.body)

    body = args.body
    if not args.no_footer:
        footer = policy.get('footer', '').strip()
        if footer:
            body = body.rstrip() + f"\n\n{footer}"

    out = run([
        GOG, '-a', account, 'gmail', 'send',
        '--to', args.to,
        '--subject', subject,
        '--body', body,
        '--plain'
    ])

    result = {'ok': True, 'account': account, 'to': args.to, 'subject': subject, 'raw': out.strip()}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"sent via {account} -> {args.to}\nsubject: {subject}\n{out.strip()}")


if __name__ == '__main__':
    main()
