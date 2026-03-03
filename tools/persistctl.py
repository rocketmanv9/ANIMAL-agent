#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.persistence_middleware import PersistConfig, PersistenceClient, diagnose_local_architecture


def main():
    ap = argparse.ArgumentParser(description='Persistence continuity controller')
    ap.add_argument('--agent', default='ANIMAL')
    sub = ap.add_subparsers(dest='cmd', required=True)

    sub.add_parser('diagnose')
    sub.add_parser('boot')

    p = sub.add_parser('step')
    p.add_argument('--summary', required=True)
    p.add_argument('--type', default='significant_step')
    p.add_argument('--payload', default='{}')

    p = sub.add_parser('shutdown')
    p.add_argument('--payload', default='{}')

    p = sub.add_parser('task-add')
    p.add_argument('--title', required=True)
    p.add_argument('--details', default='')
    p.add_argument('--type', default='one_time')
    p.add_argument('--priority', type=int, default=3)
    p.add_argument('--due-at')
    p.add_argument('--recurrence')
    p.add_argument('--depends-on')

    sub.add_parser('resurface')

    p = sub.add_parser('buffer')
    p.add_argument('--current-sprint', default='{}')
    p.add_argument('--today-tasks', default='[]')
    p.add_argument('--blockers', default='[]')
    p.add_argument('--open-loops', default='[]')

    p = sub.add_parser('reflect-eod')
    p.add_argument('--wins', required=True)
    p.add_argument('--misses', required=True)
    p.add_argument('--carry-forward', default='[]')

    p = sub.add_parser('reflect-weekly')
    p.add_argument('--wins', required=True)
    p.add_argument('--misses', required=True)
    p.add_argument('--carry-forward', default='[]')

    p = sub.add_parser('learn')
    p.add_argument('--failure', required=True)
    p.add_argument('--lesson', required=True)
    p.add_argument('--upgrade', default='')

    args = ap.parse_args()

    cfg = PersistConfig.from_env(agent_name=args.agent)
    client = PersistenceClient(cfg)

    if args.cmd == 'diagnose':
        print(json.dumps(diagnose_local_architecture(), indent=2))
        return
    if args.cmd == 'boot':
        print(json.dumps(client.boot_load(), indent=2))
        return
    if args.cmd == 'step':
        client.step_commit(args.type, args.summary, json.loads(args.payload))
        print(json.dumps({'ok': True}, indent=2))
        return
    if args.cmd == 'shutdown':
        client.shutdown_write(json.loads(args.payload))
        print(json.dumps({'ok': True}, indent=2))
        return
    if args.cmd == 'task-add':
        client.add_task(
            title=args.title,
            details=args.details,
            task_type=args.type,
            priority=args.priority,
            due_at=args.due_at,
            recurrence=args.recurrence,
            depends_on_task_id=args.depends_on,
        )
        print(json.dumps({'ok': True}, indent=2))
        return
    if args.cmd == 'resurface':
        rows = client.resurface_incomplete()
        print(json.dumps({'ok': True, 'resurfaced': rows, 'count': len(rows)}, indent=2))
        return
    if args.cmd == 'buffer':
        client.upsert_work_buffer(
            current_sprint=json.loads(args.current_sprint),
            today_tasks=json.loads(args.today_tasks),
            blockers=json.loads(args.blockers),
            open_loops=json.loads(args.open_loops),
        )
        print(json.dumps({'ok': True}, indent=2))
        return
    if args.cmd == 'reflect-eod':
        key = datetime.now().strftime('%Y-%m-%d')
        client.write_reflection('daily', key, args.wins, args.misses, json.loads(args.carry_forward))
        print(json.dumps({'ok': True, 'period_key': key}, indent=2))
        return
    if args.cmd == 'reflect-weekly':
        key = datetime.now().strftime('%G-W%V')
        client.write_reflection('weekly', key, args.wins, args.misses, json.loads(args.carry_forward))
        print(json.dumps({'ok': True, 'period_key': key}, indent=2))
        return
    if args.cmd == 'learn':
        client.log_self_improvement(args.failure, args.lesson, args.upgrade)
        print(json.dumps({'ok': True}, indent=2))
        return


if __name__ == '__main__':
    main()
