# OpenClaw Persistence Audit + Upgrade Plan

## Phase 1 — Diagnose (implemented)

### Current memory architecture
1. **Long-term memory (file-based)**
   - `MEMORY.md` (curated long-term notes)
   - `memory/YYYY-MM-DD.md` (daily logs)
2. **Session memory (runtime transcripts)**
   - `/home/grant/.openclaw/agents/main/sessions/*.jsonl`
   - lock files: `*.jsonl.lock`
3. **Operational state (ad-hoc files)**
   - `.openclaw/workspace-state.json`
   - per-tool caches (`.openclaw/weather_cache.json`, etc.)
4. **Recall layer**
   - `memory_search` uses semantic retrieval over MEMORY files/transcripts (tool-level behavior)

### What is lost between daemon restarts
- Any in-flight process state not committed to files/DB.
- Pending intentions not written to persistent task store.
- Scheduler intent if only conversational (not in cron/DB).

### What is lost between agent turns
- Ephemeral reasoning context unless written to file/session log.
- Unpersisted step-level work state.

### Transactionality of memory writes (current)
- **Weak**: mostly plain file appends/edits.
- JSONL session lock can fail (`session file locked`) causing continuity issues.
- No global transactional boundary across memory + tasks + state.

### Memory indexing / embeddings
- Semantic retrieval exists at tool layer (`memory_search`) but no explicit local embeddings/index DB under workspace ownership.

### Weak points / failure modes
- Lock contention on session jsonl.
- No canonical task table for resurfacing incomplete work.
- No structured project-state snapshots at step boundaries.
- Reflection data not normalized for recurring audits.
- Infra status loops not modeled as dependent/blocking tasks.

### Why persistence feels unreliable
- Persistence is split across markdown + session logs + ad-hoc caches.
- No single source of truth for active projects/tasks/open loops.
- No guaranteed step-commit middleware on every significant action.

---

## Phase 2 — Design Fix (implemented in schema + middleware)

### A) Long-term structured memory (Postgres/Supabase)
Tables added for:
- goals
- projects
- user_preferences
- infrastructure_state
- memory_entries

### B) Working memory buffer
Tables added for:
- working_memory_buffers (current sprint, today tasks, blockers, open loops)
- execution_steps (step-level commits)

### C) Reflection system
Tables added for:
- reflections (daily/weekly)
- self_improvement_log (failures, lessons, upgrades)

### D) Task scheduler model
Tables + fields for:
- one-time / recurring / blocking / dependent tasks
- `depends_on_task_id`
- recurrence fields (`recurrence`, `next_run_at`)
- resurfacing via `status`, `due_at`, `last_resurfaced_at`

---

## Phase 3 — Implemented artifacts
- SQL schema + migration scripts
- Python middleware for boot-load / step-commit / shutdown-write
- CLI for task + memory + reflection + resurfacing workflows

---

## Phase 4 — Continuous improvement
- `self_improvement_log` table + middleware write path (`reflect` / `learn`)

