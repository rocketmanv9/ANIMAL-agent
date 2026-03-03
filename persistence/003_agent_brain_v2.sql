BEGIN;

CREATE TABLE IF NOT EXISTS migrations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  applied_ts timestamptz NOT NULL DEFAULT now(),
  checksum text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS health_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ts timestamptz NOT NULL DEFAULT now(),
  agent_id text NOT NULL,
  level text NOT NULL,
  component text NOT NULL,
  message text NOT NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_health_events_ts ON health_events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_health_events_level_ts ON health_events(level, ts DESC);

CREATE TABLE IF NOT EXISTS agents (
  agent_id text PRIMARY KEY,
  status text NOT NULL DEFAULT 'idle',
  last_seen_ts timestamptz NOT NULL DEFAULT now(),
  heartbeat_interval_sec int NOT NULL DEFAULT 60,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS locks (
  key text PRIMARY KEY,
  owner_agent_id text NOT NULL,
  acquired_ts timestamptz NOT NULL DEFAULT now(),
  expires_ts timestamptz NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_locks_expires ON locks(expires_ts);

CREATE TABLE IF NOT EXISTS shared_context (
  key text PRIMARY KEY,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_ts timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_ts timestamptz NOT NULL DEFAULT now(),
  updated_ts timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'queued', -- queued|claimed|done|failed|dead
  job_type text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  priority int NOT NULL DEFAULT 3,
  attempts int NOT NULL DEFAULT 0,
  max_attempts int NOT NULL DEFAULT 5,
  available_at timestamptz NOT NULL DEFAULT now(),
  claimed_by text,
  claimed_ts timestamptz,
  last_error text,
  dead_letter_reason text
);
CREATE INDEX IF NOT EXISTS idx_job_queue_claim ON job_queue(status, available_at, priority);

CREATE TABLE IF NOT EXISTS skills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_name text NOT NULL UNIQUE,
  description text,
  complexity_rank int NOT NULL DEFAULT 3,
  preferred_model text,
  enabled boolean NOT NULL DEFAULT true,
  updated_ts timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS capability_scores (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_name text NOT NULL,
  model_name text NOT NULL,
  success_count int NOT NULL DEFAULT 0,
  failure_count int NOT NULL DEFAULT 0,
  avg_latency_ms int NOT NULL DEFAULT 0,
  last_outcome text,
  updated_ts timestamptz NOT NULL DEFAULT now(),
  UNIQUE(skill_name, model_name)
);

DO $$
BEGIN
  BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
  EXCEPTION WHEN others THEN
    NULL;
  END;

  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector') THEN
    EXECUTE 'ALTER TABLE memory_events ADD COLUMN IF NOT EXISTS embedding vector(1536)';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION trg_set_updated_ts()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_ts = now();
  RETURN NEW;
END; $$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='updated_ts') THEN
    BEGIN
      DROP TRIGGER IF EXISTS trg_tasks_updated_ts_v2 ON tasks;
      CREATE TRIGGER trg_tasks_updated_ts_v2 BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION trg_set_updated_ts();
    EXCEPTION WHEN others THEN
      NULL;
    END;
  END IF;
END $$;

DROP TRIGGER IF EXISTS trg_job_queue_updated_ts ON job_queue;
CREATE TRIGGER trg_job_queue_updated_ts BEFORE UPDATE ON job_queue FOR EACH ROW EXECUTE FUNCTION trg_set_updated_ts();

DROP TRIGGER IF EXISTS trg_skills_updated_ts ON skills;
CREATE TRIGGER trg_skills_updated_ts BEFORE UPDATE ON skills FOR EACH ROW EXECUTE FUNCTION trg_set_updated_ts();

DROP TRIGGER IF EXISTS trg_cap_scores_updated_ts ON capability_scores;
CREATE TRIGGER trg_cap_scores_updated_ts BEFORE UPDATE ON capability_scores FOR EACH ROW EXECUTE FUNCTION trg_set_updated_ts();

CREATE OR REPLACE FUNCTION claim_next_job(p_agent_id text)
RETURNS TABLE (
  id uuid,
  job_type text,
  payload jsonb,
  attempts int,
  max_attempts int,
  priority int
) LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  WITH next_job AS (
    SELECT jq.id
    FROM job_queue jq
    WHERE jq.status = 'queued'
      AND jq.available_at <= now()
    ORDER BY jq.priority ASC, jq.created_ts ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  )
  UPDATE job_queue q
  SET status = 'claimed',
      claimed_by = p_agent_id,
      claimed_ts = now(),
      attempts = q.attempts + 1,
      updated_ts = now()
  FROM next_job
  WHERE q.id = next_job.id
  RETURNING q.id, q.job_type, q.payload, q.attempts, q.max_attempts, q.priority;
END; $$;

CREATE OR REPLACE FUNCTION acquire_lock(p_key text, p_owner text, p_ttl_seconds int)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE
  ok boolean := false;
BEGIN
  DELETE FROM locks WHERE key = p_key AND expires_ts <= now();

  BEGIN
    INSERT INTO locks(key, owner_agent_id, acquired_ts, expires_ts)
    VALUES (p_key, p_owner, now(), now() + make_interval(secs => p_ttl_seconds));
    ok := true;
  EXCEPTION WHEN unique_violation THEN
    ok := false;
  END;

  RETURN ok;
END; $$;

CREATE OR REPLACE FUNCTION release_lock(p_key text, p_owner text)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE
  n int;
BEGIN
  DELETE FROM locks WHERE key = p_key AND owner_agent_id = p_owner;
  GET DIAGNOSTICS n = ROW_COUNT;
  RETURN n > 0;
END; $$;

INSERT INTO migrations(name, checksum, metadata)
VALUES ('003_agent_brain_v2.sql', 'agent_brain_v2', '{"phase":"foundation"}'::jsonb)
ON CONFLICT (name) DO NOTHING;

COMMIT;
