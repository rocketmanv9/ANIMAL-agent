# OpenClaw Persistence Layer

Implemented components:
- `001_persistence_schema.sql` (Postgres/Supabase schema)
- `tools/persistence_middleware.py` (boot/step/shutdown/task/reflection middleware)
- `tools/persistctl.py` (CLI)
- `tools/persistence_scheduler.sh` (resurfacing loop)

## Data model covers
- Long-term memory: goals, projects, preferences, infra state, memory entries
- Working memory: sprint, today tasks, blockers, open loops
- Reflection: daily/weekly with carry-forward
- Task scheduler: one-time/recurring/blocking/dependent
- Self-improvement: failure→lesson→upgrade tracking

## Notes
- Remote mode uses Supabase PostgREST if `SUPABASE_SERVICE_ROLE_KEY` + URL are present.
- If remote is unavailable, middleware uses atomic local fallback file at:
  `.openclaw/persist_fallback.json`
- Atomic fallback uses temp-file + `os.replace` for transactional local writes.
