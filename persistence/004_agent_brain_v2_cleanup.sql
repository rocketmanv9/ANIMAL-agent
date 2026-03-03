BEGIN;

-- 1) Deduplicate tasks by (title, description), keep newest
WITH ranked AS (
  SELECT id, title, coalesce(description,'' ) AS d, updated_ts,
         row_number() OVER (PARTITION BY title, coalesce(description,'') ORDER BY updated_ts DESC NULLS LAST, created_ts DESC NULLS LAST, id DESC) AS rn
  FROM tasks
)
DELETE FROM tasks t
USING ranked r
WHERE t.id = r.id
  AND r.rn > 1;

-- 2) Normalize blocked infra tasks into awaiting user input metadata
UPDATE tasks
SET status = 'blocked',
    blockers = CASE
      WHEN jsonb_typeof(blockers) = 'array' THEN blockers
      ELSE '[]'::jsonb
    END || to_jsonb(ARRAY['awaiting_user_input']::text[]),
    last_review_ts = now(),
    updated_ts = now()
WHERE lower(coalesce(description,'')) LIKE '%infra%confirm%'
   OR lower(coalesce(title,'')) LIKE '%infra%confirm%';

INSERT INTO migrations(name, checksum, metadata)
VALUES ('004_agent_brain_v2_cleanup.sql','agent_brain_v2_cleanup','{"phase":"cleanup"}'::jsonb)
ON CONFLICT (name) DO NOTHING;

COMMIT;
