import { getDb } from '@/lib/db';

export async function GET() {
  try {
    const db = getDb();

    const [skills, blocked, overdue, unreviewed, agent, health, jobs] = await Promise.all([
      db.query(`select skill_name, complexity_rank, preferred_model, enabled, updated_ts from skills order by skill_name`),
      db.query(`select id,title,priority from tasks where coalesce(status,'todo')='blocked' order by priority asc, coalesce(updated_ts,created_ts,created_at) desc limit 20`),
      db.query(`select id,title,priority,coalesce(due_ts,due_at) as due_ts from tasks where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked') and coalesce(due_ts,due_at) < now() order by priority asc limit 20`),
      db.query(`select id,title,priority,last_review_ts from tasks where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked') and (last_review_ts is null or last_review_ts < now()- interval '7 days') order by priority asc limit 20`),
      db.query(`select agent_id,status,last_seen_ts,heartbeat_interval_sec,metadata from agents order by last_seen_ts desc limit 5`),
      db.query(`select ts,level,component,message from health_events order by ts desc limit 30`),
      db.query(`select status, count(*)::int as n from job_queue group by status order by status`)
    ]);

    return Response.json({
      ok: true,
      tools: skills.rows,
      openLoops: {
        blocked: blocked.rows,
        overdue: overdue.rows,
        unreviewed7d: unreviewed.rows
      },
      agents: agent.rows,
      health: health.rows,
      jobs: jobs.rows
    });
  } catch (e) {
    return Response.json({ ok: false, error: e.message }, { status: 500 });
  }
}
