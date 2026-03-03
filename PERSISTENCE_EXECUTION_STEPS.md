# Persistence Execution Steps (Implemented)

## 1) Diagnose
```bash
python3 tools/persistctl.py diagnose
```

## 2) Apply DB schema (Supabase/Postgres)
```bash
# run in SQL editor or psql
# file: persistence/001_persistence_schema.sql
```

## 3) Boot load (middleware) + mandatory open-loop summary
```bash
python3 tools/persistctl.py boot
python3 tools/persistctl.py startup-summary
```

## 4) Commit significant step
```bash
python3 tools/persistctl.py step \
  --type significant_step \
  --summary "Implemented marketing event handler" \
  --payload '{"repo":"mountain-valley-storage","branch":"ANIMAL"}'
```

## 5) Upsert working memory buffer
```bash
python3 tools/persistctl.py buffer \
  --current-sprint '{"name":"EDA hardening"}' \
  --today-tasks '[{"title":"Fix event processor"}]' \
  --blockers '[]' \
  --open-loops '[{"title":"validate cron"}]'
```

## 6) Add scheduled/dependent tasks
```bash
python3 tools/persistctl.py task-add --title "Run nightly marketing checks" --type recurring --recurrence "daily"
python3 tools/persistctl.py task-add --title "Confirm infra migration applied" --type blocking --depends-on "<task-id>"
```

## 7) Resurface + reevaluate open loops (every 6h)
```bash
python3 tools/persistctl.py resurface
python3 tools/persistctl.py reevaluate --stale-hours 6
```

If reevaluate returns:
- `ask_for_direction=true` → ask user for direction immediately.
- `infra_confirmation_needed` entries → ask for infra status confirmation before stalling.
- `credential_prompts` entries → prompt clearly for required credentials/scopes.

## 8) Daily + weekly reflections
```bash
python3 tools/persistctl.py reflect-eod --wins "Shipped persistence schema" --misses "Missed 30-min cadence" --carry-forward '[{"task":"cadence enforcement"}]'
python3 tools/persistctl.py reflect-weekly --wins "Improved continuity" --misses "Session lock incidents" --carry-forward '[{"task":"lock recovery"}]'
```

## 9) Self-improvement log
```bash
python3 tools/persistctl.py learn \
  --failure "Session lock timeout" \
  --lesson "Need atomic fallback + resumable queue" \
  --upgrade "Added atomic local fallback in middleware"
```

## 10) Shutdown write
```bash
python3 tools/persistctl.py shutdown --payload '{"status":"clean","next":"resume blocked tasks"}'
```
