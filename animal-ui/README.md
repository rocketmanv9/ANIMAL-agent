# ANIMAL UI

## Features
- Tools registry from DB (`skills`)
- Open loops (`tasks` blocked/overdue/unreviewed)
- Agent heartbeat (`agents`)
- Health stream (`health_events`)
- Chat request panel (logs into `memory_events` + creates `tasks`)
- Tool propose/execute actions (`tasks` / `job_queue`)

## Run
```bash
npm install
npm run dev
```

## Required env
- `DATABASE_URL`

## Deploy (Vercel)
- Import repo
- Set `DATABASE_URL`
- Build command: `npm run build`
- Start command: `npm run start`
