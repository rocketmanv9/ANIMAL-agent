#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from camera.core import (
    detect_environment,
    list_devices,
    capture_image,
    record_clip,
    who_is_using,
    ensure_consent,
    set_consent,
)


def main():
    ap = argparse.ArgumentParser(description='OpenClaw camera CLI')
    sub = ap.add_subparsers(dest='cmd', required=True)

    sub.add_parser('env')
    sub.add_parser('list')

    p = sub.add_parser('consent')
    p.add_argument('--grant', action='store_true')
    p.add_argument('--revoke', action='store_true')

    p = sub.add_parser('snap')
    p.add_argument('--out', required=True)
    p.add_argument('--device')

    p = sub.add_parser('clip')
    p.add_argument('--out', required=True)
    p.add_argument('--seconds', type=int, default=5)
    p.add_argument('--device')

    p = sub.add_parser('who')
    p.add_argument('--device', default='/dev/video0')

    args = ap.parse_args()

    if args.cmd == 'env':
        print(json.dumps(detect_environment(), indent=2))
        return
    if args.cmd == 'list':
        print(json.dumps(list_devices(), indent=2))
        return
    if args.cmd == 'consent':
        if args.grant:
            print(json.dumps(set_consent(True), indent=2))
        elif args.revoke:
            print(json.dumps(set_consent(False), indent=2))
        else:
            print(json.dumps({'consent_granted': ensure_consent()}, indent=2))
        return
    if args.cmd == 'snap':
        res = capture_image(args.out, device=args.device)
        print(json.dumps(res, indent=2))
        return
    if args.cmd == 'clip':
        res = record_clip(args.out, seconds=args.seconds, device=args.device)
        print(json.dumps(res, indent=2))
        return
    if args.cmd == 'who':
        print(json.dumps(who_is_using(args.device), indent=2))


if __name__ == '__main__':
    main()
