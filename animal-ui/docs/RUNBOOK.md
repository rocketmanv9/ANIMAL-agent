# Operations Runbook

## Local dev
```bash
cd animal-ui
npm install
npm run dev
```

## Build test
```bash
cd animal-ui
npm run build
```

## Runtime checks
```bash
# DB/runtime health
curl http://localhost:3000/api/health

# Agent boot/tick
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js boot
node /home/grant/.openclaw/workspace/tools/agent_brain_v2.js tick

# Open loops
node /home/grant/.openclaw/workspace/tools/open_loop_scanner_v2.js
```

## Scheduler
- Tick every 5 minutes
- Open-loop scan every 6 hours

Check current crontab:
```bash
crontab -l
```

## If deploy fails and you're on phone only
1. Ensure Vercel root directory = `animal-ui`
2. Confirm env vars exist (`DATABASE_URL`, `ANIMAL_UI_EMAIL`, `ANIMAL_UI_PASSCODE`)
3. Ask someone to open `/api/health` and report `missing` fields
