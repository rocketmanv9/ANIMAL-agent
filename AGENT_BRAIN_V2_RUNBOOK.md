# Agent Brain V2 Runbook

## Apply migrations
```bash
set -a; source /home/grant/.openclaw/workspace/.env; set +a
node /home/grant/.openclaw/workspace/tools/run_sql_migrations.js \
  /home/grant/.openclaw/workspace/persistence/001_persistence_schema.sql \
  /home/grant/.openclaw/workspace/persistence/002_openclaw_persistence_v1.sql \
  /home/grant/.openclaw/workspace/persistence/003_agent_brain_v2.sql
```

## Phase 1 smoke
```bash
set -a; source /home/grant/.openclaw/workspace/.env; set +a
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js phase1
```

## Boot hydration + open loops
```bash
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js boot
python3 /home/grant/.openclaw/workspace/tools/open_loop_scanner.py
```

## Task engine
```bash
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js create-task "Follow up blocked migration" "ask user for pooler route" 1
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js resurface
```

## Retry queue / heartbeat
```bash
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js tick
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js loop 3
```

## Skills / routing
```bash
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js register-skill "db_migration" "transactional schema ops" 5 "openai-codex/gpt-5.3-codex"
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js skill-outcome "db_migration" "openai-codex/gpt-5.3-codex" true 1200
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js route "complex architecture migration"
```

## Weekly review
```bash
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js weekly-review
```

## External scheduler mode
Use cron/systemd to execute `tick` every 1-5 minutes.

Example cron:
```cron
*/5 * * * * . /home/grant/.openclaw/workspace/.env && node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js tick >> /tmp/agent_brain_tick.log 2>&1
```
