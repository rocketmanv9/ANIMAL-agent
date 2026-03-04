# Current Status

## Working
- Agent Brain V2 schema + runtime operational
- Job queue claim/retry/dead-letter path verified
- Open-loop scanner operational
- UI dashboard + login gate implemented
- Tools registry reflected in DB skills table

## Pending / watch
- Real semantic embeddings pending real embedding credentials
- Continue UI hardening based on production feedback

## Last known deploy blockers
- Vercel 404 likely root directory mismatch
- API 500 likely missing `DATABASE_URL`
- login loops likely missing auth envs
