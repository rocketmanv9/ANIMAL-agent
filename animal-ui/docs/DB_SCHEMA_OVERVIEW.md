# DB Schema Overview (Agent Brain V2)

## Task + memory continuity
- `tasks`
  - lifecycle: `todo|doing|blocked|done`
  - supports blockers, recurrence, due timestamps, review tracking
- `memory_events`
  - structured event log for decisions/facts/errors/actions

## Runtime state
- `agent_state`
  - latest JSON snapshot for agent context
- `agents`
  - heartbeat status and last seen
- `locks`
  - distributed lock entries to avoid concurrent execution conflicts

## Reliability + queueing
- `job_queue`
  - queued/claimed/done/failed/dead
  - retries + max attempts
- `health_events`
  - system-level operational logs
- `heartbeat_ticks`
  - proof of scheduler activity over time

## Intelligence/routing
- `skills`
  - registered tool/skill catalog
- `capability_scores`
  - per-model outcomes for routing decisions

## Coordination
- `shared_context`
  - deduped notification markers and shared signaling
- `reflections`
  - daily/weekly retrospectives
- `migrations`
  - migration tracking

## Useful operator queries
```sql
-- open loops
select id,title,status,priority from tasks
where status in ('todo','doing','blocked')
order by priority asc;

-- latest health issues
select ts,level,component,message from health_events
order by ts desc
limit 50;

-- heartbeat proof
select count(*) as ticks_10m, min(ts), max(ts)
from heartbeat_ticks
where ts > now() - interval '10 minutes';

-- dead-letter jobs
select id,job_type,attempts,max_attempts,last_error,dead_letter_reason
from job_queue
where status='dead'
order by updated_ts desc;
```
