# UI Architecture

## Pages
- `/login`
  - simple gate using env-provided email + passcode
- `/`
  - command center dashboard

## API routes
- `/api/health`
  - validates required env vars for production runtime
- `/api/dashboard`
  - aggregates tools/open loops/agents/health/jobs from DB
- `/api/chat`
  - ingests user message into DB for agent processing
- `/api/tool-action`
  - `propose` -> task
  - `execute` -> queued job

## Middleware
- `middleware.js`
  - blocks all routes except login/auth/static without valid session cookie

## Data flow
1) User enters request in UI.
2) Request written to DB (`memory_events`, `tasks` or `job_queue`).
3) Agent heartbeat loop consumes jobs/tasks.
4) Agent writes outputs/health/state back to DB.
5) UI refreshes dashboard from `/api/dashboard`.

## Deployment notes
- For Vercel, set root directory to `animal-ui`.
- Env vars must be in Production scope.
- Use `/api/health` post-deploy to confirm runtime readiness.
