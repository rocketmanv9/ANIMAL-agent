# ANIMAL Agent Handoff

## Identity
- Agent: **ANIMAL / Clawbot**
- Role: persistent autonomous systems operator + execution assistant
- Runtime: OpenClaw main agent
- Primary repo: `ANIMAL-agent`

## What this project is
This UI is the operational frontend for Agent Brain V2:
- tool registry visibility
- open loop tracking
- health/event monitoring
- controlled action proposals/executions
- chat ingress into agent task pipeline

## Core architecture
1. **UI (Next.js)**
   - Path: `animal-ui/`
   - Routes:
     - `/` dashboard
     - `/login` forced auth
     - `/api/dashboard` DB-backed status summary
     - `/api/chat` writes user request into DB (`memory_events` + `tasks`)
     - `/api/tool-action` creates proposal task or execution job
     - `/api/health` env readiness endpoint

2. **DB (Supabase Postgres)**
   - Persistence schema files:
     - `persistence/001_persistence_schema.sql`
     - `persistence/002_openclaw_persistence_v1.sql`
     - `persistence/003_agent_brain_v2.sql`
     - `persistence/004_agent_brain_v2_cleanup.sql`
     - `persistence/005_agent_brain_v2_hardening.sql`
   - Key tables:
     - `tasks`, `memory_events`, `agent_state`, `reflections`
     - `job_queue`, `health_events`, `agents`, `locks`, `skills`, `capability_scores`, `shared_context`, `heartbeat_ticks`, `migrations`

3. **Runtime (Agent Brain V2)**
   - `tools/agent_brain_v2.js`
   - Tick loop:
     1) heartbeat update
     2) lock acquire
     3) claim/execute one job
     4) resurface overdue/blocked if no job
     5) write state snapshot
     6) log health

## Security model
- UI is protected by middleware + login gate.
- Required env:
  - `DATABASE_URL`
  - `ANIMAL_UI_EMAIL`
  - `ANIMAL_UI_PASSCODE`
- Session cookie: `animal_session`

## Current known gap
- Real semantic embeddings (GAP 1) requires real embedding credentials (`OPENAI_API_KEY`).
- Without that, system runs fully but semantic vector search remains incomplete by strict spec.

## Handoff checklist for next agent
1. Verify DB health:
   - `node tools/agent_brain_v2.js phase1`
2. Verify heartbeat:
   - `node tools/agent_brain_v2.js tick`
   - check `heartbeat_ticks`
3. Verify UI health:
   - `GET /api/health`
4. Verify auth gate:
   - visit `/` unauthenticated -> redirects `/login`
5. Continue from open loops:
   - run `node tools/open_loop_scanner_v2.js`

## Change discipline
- Small commits
- Smoke test after each change
- Log failures in `health_events`
- Create task when blocked
