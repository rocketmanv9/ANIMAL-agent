#!/usr/bin/env python3
"""OpenClaw persistence middleware (Supabase/Postgres via PostgREST).

Implements:
- boot load
- step commit
- shutdown write
- task lifecycle + resurfacing
- reflections + self-improvement logging
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import parse, request, error


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PersistConfig:
    supabase_url: Optional[str]
    service_key: Optional[str]
    agent_name: str = 'ANIMAL'
    local_fallback_path: Path = Path('/home/grant/.openclaw/workspace/.openclaw/persist_fallback.json')

    @staticmethod
    def from_env(agent_name: str = 'ANIMAL') -> 'PersistConfig':
        return PersistConfig(
            supabase_url=os.getenv('NEXT_PUBLIC_SUPABASE_URL') or os.getenv('SUPABASE_URL'),
            service_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
            agent_name=agent_name,
        )


class PersistenceClient:
    def __init__(self, cfg: PersistConfig):
        self.cfg = cfg

    # ---------- low-level ----------
    def _has_remote(self) -> bool:
        return bool(self.cfg.supabase_url and self.cfg.service_key)

    def _remote_headers(self) -> Dict[str, str]:
        return {
            'apikey': self.cfg.service_key or '',
            'Authorization': f'Bearer {self.cfg.service_key or ""}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
        }

    def _rest(self, method: str, table: str, payload: Optional[dict] = None, query: str = '') -> Any:
        if not self._has_remote():
            raise RuntimeError('Remote persistence not configured')
        base = self.cfg.supabase_url.rstrip('/')
        url = f"{base}/rest/v1/{table}"
        if query:
            url += ('?' + query)
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        req = request.Request(url, method=method, data=data, headers=self._remote_headers())
        try:
            with request.urlopen(req, timeout=20) as r:
                txt = r.read().decode('utf-8', errors='replace')
                return json.loads(txt) if txt else None
        except error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'{method} {table} failed: {e.code} {msg}')

    def _local_read(self) -> dict:
        p = self.cfg.local_fallback_path
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return {
            'execution_steps': [],
            'working_memory_buffers': {},
            'tasks': [],
            'reflections': [],
            'self_improvement_log': [],
            'memory_entries': [],
            'infrastructure_state': {},
        }

    def _local_write_atomic(self, state: dict) -> None:
        p = self.cfg.local_fallback_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', delete=False, dir=str(p.parent), encoding='utf-8') as tf:
            json.dump(state, tf, indent=2)
            tmp = tf.name
        os.replace(tmp, p)

    # ---------- middleware actions ----------
    def boot_load(self) -> dict:
        summary = {
            'agent_name': self.cfg.agent_name,
            'loaded_at': utc_now_iso(),
            'source': 'remote' if self._has_remote() else 'local_fallback',
        }
        self.step_commit('boot', 'boot load', {'source': summary['source']})
        return summary

    def step_commit(self, step_type: str, summary: str, payload: Optional[dict] = None) -> None:
        payload = payload or {}
        if self._has_remote():
            self._rest('POST', 'execution_steps', {
                'agent_name': self.cfg.agent_name,
                'step_type': step_type,
                'summary': summary,
                'payload': payload,
            })
            return

        st = self._local_read()
        st['execution_steps'].append({
            'agent_name': self.cfg.agent_name,
            'step_type': step_type,
            'summary': summary,
            'payload': payload,
            'created_at': utc_now_iso(),
        })
        self._local_write_atomic(st)

    def shutdown_write(self, state_payload: dict) -> None:
        self.step_commit('shutdown', 'shutdown snapshot', state_payload)

    def upsert_work_buffer(self, current_sprint: dict, today_tasks: List[dict], blockers: List[dict], open_loops: List[dict]) -> None:
        if self._has_remote():
            # upsert by agent_name via REST conflict target
            q = parse.urlencode({'on_conflict': 'agent_name'})
            self._rest('POST', 'working_memory_buffers', {
                'agent_name': self.cfg.agent_name,
                'current_sprint': current_sprint,
                'today_tasks': today_tasks,
                'blocking_issues': blockers,
                'open_loops': open_loops,
            }, query=q)
            return

        st = self._local_read()
        st['working_memory_buffers'][self.cfg.agent_name] = {
            'current_sprint': current_sprint,
            'today_tasks': today_tasks,
            'blocking_issues': blockers,
            'open_loops': open_loops,
            'updated_at': utc_now_iso(),
        }
        self._local_write_atomic(st)

    def add_task(self, title: str, details: str = '', task_type: str = 'one_time', status: str = 'open',
                 priority: int = 3, due_at: Optional[str] = None, recurrence: Optional[str] = None,
                 depends_on_task_id: Optional[str] = None, metadata: Optional[dict] = None) -> None:
        row = {
            'title': title,
            'details': details,
            'task_type': task_type,
            'status': status,
            'priority': priority,
            'due_at': due_at,
            'recurrence': recurrence,
            'depends_on_task_id': depends_on_task_id,
            'metadata': metadata or {},
        }
        if self._has_remote():
            self._rest('POST', 'tasks', row)
            return

        st = self._local_read()
        row['id'] = f"local-{len(st['tasks'])+1}"
        row['created_at'] = utc_now_iso()
        row['updated_at'] = utc_now_iso()
        st['tasks'].append(row)
        self._local_write_atomic(st)

    def resurface_incomplete(self) -> List[dict]:
        now = datetime.now(timezone.utc)
        resurfaced: List[dict] = []

        if self._has_remote():
            # fetch open/in_progress/blocked tasks ordered by due
            q = parse.urlencode({
                'select': 'id,title,status,due_at,recurrence,resurfacing_count,last_resurfaced_at',
                'status': 'in.(open,in_progress,blocked)',
                'order': 'due_at.asc.nullslast',
            }, safe='().,')
            rows = self._rest('GET', 'tasks', query=q) or []
            for r in rows:
                due = r.get('due_at')
                should = False
                if due:
                    try:
                        due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                        should = due_dt <= now
                    except Exception:
                        should = True
                else:
                    should = True
                if should:
                    resurfaced.append(r)
                    self._rest('PATCH', 'tasks', {
                        'resurfacing_count': int(r.get('resurfacing_count') or 0) + 1,
                        'last_resurfaced_at': utc_now_iso(),
                    }, query=f"id=eq.{r['id']}")
            return resurfaced

        st = self._local_read()
        for t in st['tasks']:
            if t.get('status') not in ('open', 'in_progress', 'blocked'):
                continue
            due_at = t.get('due_at')
            should = False
            if due_at:
                try:
                    due_dt = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                    should = due_dt <= now
                except Exception:
                    should = True
            else:
                should = True
            if should:
                t['resurfacing_count'] = int(t.get('resurfacing_count') or 0) + 1
                t['last_resurfaced_at'] = utc_now_iso()
                t['updated_at'] = utc_now_iso()
                resurfaced.append(t)
        self._local_write_atomic(st)
        return resurfaced

    def write_reflection(self, period_type: str, period_key: str, wins: str, misses: str, carry_forward: List[dict]) -> None:
        row = {
            'agent_name': self.cfg.agent_name,
            'period_type': period_type,
            'period_key': period_key,
            'wins': wins,
            'misses': misses,
            'carry_forward': carry_forward,
        }
        if self._has_remote():
            q = parse.urlencode({'on_conflict': 'agent_name,period_type,period_key'})
            self._rest('POST', 'reflections', row, query=q)
            return

        st = self._local_read()
        st['reflections'].append({**row, 'created_at': utc_now_iso()})
        self._local_write_atomic(st)

    def log_self_improvement(self, failure: str, lesson: str, upgrade_applied: str = '') -> None:
        row = {
            'agent_name': self.cfg.agent_name,
            'failure': failure,
            'lesson': lesson,
            'upgrade_applied': upgrade_applied,
        }
        if self._has_remote():
            self._rest('POST', 'self_improvement_log', row)
            return

        st = self._local_read()
        st['self_improvement_log'].append({**row, 'created_at': utc_now_iso()})
        self._local_write_atomic(st)


def diagnose_local_architecture() -> dict:
    workspace = Path('/home/grant/.openclaw/workspace')
    sessions_dir = Path('/home/grant/.openclaw/agents/main/sessions')
    return {
        'long_term_memory_paths': [str(workspace / 'MEMORY.md'), str(workspace / 'memory')],
        'session_memory_paths': [str(sessions_dir)],
        'workspace_state_paths': [str(workspace / '.openclaw/workspace-state.json')],
        'transactional_writes': 'file-based mostly non-transactional except atomic replace in fallback middleware',
        'embedding_index': 'tool-level semantic retrieval exists (memory_search); no explicit local vector table by default',
    }
