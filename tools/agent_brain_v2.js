#!/usr/bin/env node
/* Agent Brain V2 runtime */
const { Client } = require('pg');

function nowIso() { return new Date().toISOString(); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

class AgentBrain {
  constructor({ agentId = 'ANIMAL', dbUrl = process.env.DATABASE_URL }) {
    this.agentId = agentId;
    this.dbUrl = dbUrl;
    this.client = new Client({ connectionString: dbUrl, ssl: { rejectUnauthorized: false } });
  }

  async connect() { await this.client.connect(); }
  async close() { await this.client.end(); }

  async hasColumn(table, column) {
    const r = await this.client.query(
      `select exists(select 1 from information_schema.columns where table_name=$1 and column_name=$2) as ok`,
      [table, column]
    );
    return !!r.rows[0]?.ok;
  }


  async logHealth(level, component, message, details = {}) {
    try {
      await this.client.query(
        `insert into health_events(agent_id, level, component, message, details) values ($1,$2,$3,$4,$5)`,
        [this.agentId, level, component, message, details]
      );
      console.log(`[health:${level}] ${component} ${message}`);
    } catch (e) {
      console.error(`[health-log-fail] ${e.message}`);
    }
  }

  async validateConnectivity() {
    try {
      const r = await this.client.query('select now() as now');
      await this.logHealth('info', 'connectivity', 'supabase connectivity pass', { now: r.rows[0]?.now });
      return { ok: true };
    } catch (e) {
      await this.logHealth('critical', 'connectivity', 'supabase connectivity fail', { error: e.message });
      return { ok: false, error: e.message };
    }
  }

  async applyMigrations() {
    const fs = require('fs');
    const files = [
      '/home/grant/.openclaw/workspace/persistence/001_persistence_schema.sql',
      '/home/grant/.openclaw/workspace/persistence/002_openclaw_persistence_v1.sql',
      '/home/grant/.openclaw/workspace/persistence/003_agent_brain_v2.sql',
    ];

    for (const f of files) {
      const sql = fs.readFileSync(f, 'utf8');
      await this.client.query(sql);
      await this.logHealth('info', 'migration', 'migration applied', { file: f });
    }
  }

  async appendMemory(source, type, content, tags = {}) {
    await this.client.query(
      `insert into memory_events(agent_id, source, type, content, tags) values ($1,$2,$3,$4,$5)`,
      [this.agentId, source, type, content, tags]
    );

    // Auto-embed decision/fact/error if vector enabled and embeddings available
    if (!['decision', 'fact', 'error'].includes(type)) return;
    try {
      const hasVector = await this.client.query(`select exists(select 1 from information_schema.columns where table_name='memory_events' and column_name='embedding') as ok`);
      if (!hasVector.rows[0]?.ok) return;
      // Placeholder embedding generator (deterministic hash vector fallback)
      const vec = this._fakeEmbedding(content, 32); // keep small; cast into vector text
      const r = await this.client.query(`select id from memory_events where agent_id=$1 order by ts desc limit 1`, [this.agentId]);
      const id = r.rows[0]?.id;
      if (!id) return;
      await this.client.query(`update memory_events set embedding = $2::vector where id = $1`, [id, `[${vec.join(',')}]`]);
    } catch (e) {
      await this.logHealth('warning', 'memory', 'embedding skipped', { error: e.message });
    }
  }

  _fakeEmbedding(text, n = 32) {
    const out = new Array(n).fill(0);
    for (let i = 0; i < text.length; i++) out[i % n] += ((text.charCodeAt(i) % 31) - 15) / 100;
    return out.map(v => Number(v.toFixed(6)));
  }

  async queryMemory(queryText, topK = 5) {
    // semantic-ish fallback by ilike if pgvector search not configured to same dimensions
    const q = `%${queryText}%`;
    const r = await this.client.query(
      `select id, ts, type, content, tags from memory_events where content ilike $1 order by ts desc limit $2`,
      [q, topK]
    );
    return r.rows;
  }

  async bootHydrate() {
    await this.client.query(
      `insert into agents(agent_id, status, last_seen_ts) values($1,'booting',now())
       on conflict (agent_id) do update set status='booting', last_seen_ts=now()`,
      [this.agentId]
    );

    const state = await this.client.query(`select json_state from agent_state where agent_id=$1`, [this.agentId]);
    const tasks = await this.client.query(
      `select id,title,status,priority,due_at,due_ts,last_review_ts,updated_at,task_type from tasks
       where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked')
       order by priority asc, coalesce(due_ts,due_at) asc nulls last limit 10`
    );
    const mem = await this.client.query(`select ts,type,content from memory_events order by ts desc limit 20`);
    const reflTs = (await this.hasColumn('reflections','ts')) ? 'ts' : ((await this.hasColumn('reflections','created_at')) ? 'created_at' : 'id');
    const refl = await this.client.query(`select * from reflections order by ${reflTs} desc limit 1`);

    const openLoops = await this.openLoopsSummary();
    await this.logHealth('info', 'boot', 'boot hydration complete', { openLoops });

    return {
      agent_state: state.rows[0]?.json_state || {},
      open_tasks: tasks.rows,
      recent_memory: mem.rows,
      last_reflection: refl.rows[0] || null,
      open_loops: openLoops,
    };
  }

  async createTask(title, description = '', priority = 3, dueTs = null, recurrence = null) {
    await this.client.query(
      `insert into tasks(status,priority,title,description,due_ts,recurrence,last_review_ts)
       values('todo',$1,$2,$3,$4,$5,now())`,
      [priority, title, description, dueTs, recurrence]
    );
    await this.appendMemory('task_engine', 'decision', `Created task: ${title}`, { priority, recurrence });
  }

  async completeTask(id) {
    await this.client.query(`update tasks set status='done', last_review_ts=now() where id=$1`, [id]);
    await this.appendMemory('task_engine', 'fact', `Completed task ${id}`);
  }

  async blockTask(id, reason) {
    await this.client.query(
      `update tasks set status='blocked', blockers = coalesce(blockers,'[]'::jsonb) || to_jsonb(array[$2]::text[]), last_review_ts=now() where id=$1`,
      [id, reason]
    );
    await this.appendMemory('task_engine', 'error', `Blocked task ${id}: ${reason}`);
  }

  async resurfaceOverdueTasks() {
    const r = await this.client.query(
      `update tasks set status='open', last_review_ts=now(), updated_at=now()
       where (
         (coalesce(status,'todo') in ('todo','doing','in_progress','blocked','open') and coalesce(due_ts,due_at) is not null and coalesce(due_ts,due_at) < now())
         or (coalesce(status,'todo')='blocked')
         or (coalesce(status,'todo') in ('todo','doing','in_progress','open') and (last_review_ts is null or last_review_ts < now() - interval '7 days'))
       )
       returning id,title,status`
    );
    if (r.rows.length) {
      await this.appendMemory('task_engine', 'decision', `Resurfaced ${r.rows.length} tasks`, { task_ids: r.rows.map(x=>x.id) });
    }
    return r.rows;
  }

  async enqueueJob(jobType, payload = {}, priority = 3, maxAttempts = 5) {
    await this.client.query(
      `insert into job_queue(job_type,payload,priority,max_attempts,status,available_at) values($1,$2,$3,$4,'queued',now())`,
      [jobType, payload, priority, maxAttempts]
    );
  }

  async claimNextJob() {
    const r = await this.client.query(`select * from claim_next_job($1)`, [this.agentId]);
    return r.rows[0] || null;
  }

  async completeJob(id) {
    await this.client.query(`update job_queue set status='done', updated_ts=now() where id=$1`, [id]);
  }

  async failJob(id, errMsg) {
    const r = await this.client.query(`select attempts,max_attempts from job_queue where id=$1`, [id]);
    const attempts = r.rows[0]?.attempts || 1;
    const maxAttempts = r.rows[0]?.max_attempts || 5;

    if (attempts >= maxAttempts) {
      await this.client.query(
        `update job_queue set status='dead', dead_letter_reason=$2, updated_ts=now() where id=$1`,
        [id, errMsg]
      );
      await this.createTask(`Dead letter job: ${id}`, `Job exceeded retries: ${errMsg}`, 1);
      await this.logHealth('critical', 'job_queue', 'dead letter job', { job_id: id, error: errMsg });
      return;
    }

    const backoff = Math.min(3600, Math.pow(2, attempts) * 30 + Math.floor(Math.random() * 15));
    await this.client.query(
      `update job_queue
       set status='queued',
           available_at = now() + ($2 || ' seconds')::interval,
           last_error=$3,
           updated_ts=now()
       where id=$1`,
      [id, String(backoff), errMsg]
    );
  }

  async registerSkill(skillName, description = '', complexityRank = 3, preferredModel = null) {
    await this.client.query(
      `insert into skills(skill_name,description,complexity_rank,preferred_model,enabled)
       values($1,$2,$3,$4,true)
       on conflict (skill_name) do update set description=excluded.description, complexity_rank=excluded.complexity_rank, preferred_model=excluded.preferred_model, updated_ts=now()`,
      [skillName, description, complexityRank, preferredModel]
    );
  }

  async checkSkillHealth(skillName) {
    const r = await this.client.query(
      `select skill_name, model_name, success_count, failure_count,
              case when (success_count+failure_count)=0 then 0 else success_count::float/(success_count+failure_count) end as success_rate
       from capability_scores where skill_name=$1 order by success_rate desc`,
      [skillName]
    );
    return r.rows;
  }

  async recordSkillOutcome(skillName, modelName, ok, latencyMs = 0) {
    await this.client.query(
      `insert into capability_scores(skill_name, model_name, success_count, failure_count, avg_latency_ms, last_outcome)
       values($1,$2,$3,$4,$5,$6)
       on conflict (skill_name, model_name)
       do update set
         success_count = capability_scores.success_count + $3,
         failure_count = capability_scores.failure_count + $4,
         avg_latency_ms = case
           when capability_scores.avg_latency_ms = 0 then $5
           else ((capability_scores.avg_latency_ms + $5) / 2)
         end,
         last_outcome = $6,
         updated_ts = now()`,
      [skillName, modelName, ok ? 1 : 0, ok ? 0 : 1, latencyMs, ok ? 'success' : 'failure']
    );
  }

  async routingDecision(goal) {
    const complex = /architecture|migration|distributed|multi-agent|schema|pipeline/i.test(goal);
    const rows = await this.client.query(
      `select skill_name, model_name, success_count, failure_count, avg_latency_ms,
              case when (success_count+failure_count)=0 then 0 else success_count::float/(success_count+failure_count) end as success_rate,
              case when (success_count+failure_count)=0 then 0 else failure_count::float/(success_count+failure_count) end as error_rate
       from capability_scores
       order by success_rate desc, error_rate asc, avg_latency_ms asc`
    );
    const filtered = rows.rows.filter(r => r.error_rate <= 0.4);
    const best = filtered[0] || rows.rows[0] || null;
    if (!best) return { model: complex ? 'strongest' : 'cheap', reason: 'no history' };

    if (complex) return { model: best.model_name, reason: 'complex_goal_prefers_strongest_success' };
    // simple: choose lower latency among decent performers
    const simple = filtered.filter(r => r.success_rate >= 0.6).sort((a,b)=>a.avg_latency_ms-b.avg_latency_ms)[0] || best;
    return { model: simple.model_name, reason: 'simple_goal_prefers_cheaper_faster' };
  }

  async openLoopsSummary() {
    const blocked = await this.client.query(`select id,title from tasks where coalesce(status,'todo')='blocked' order by priority asc limit 20`);
    const overdue = await this.client.query(`select id,title from tasks where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked') and coalesce(due_ts,due_at) < now() order by priority asc limit 20`);
    const stale = await this.client.query(`select id,title from tasks where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked') and (last_review_ts is null or last_review_ts < now()- interval '7 days') order by priority asc limit 20`);
    return {
      blocked: blocked.rows,
      overdue: overdue.rows,
      unreviewed_7d: stale.rows,
    };
  }

  async acquireHeartbeatLock(ttlSec = 120) {
    const r = await this.client.query(`select acquire_lock($1,$2,$3) as ok`, ['heartbeat', this.agentId, ttlSec]);
    return !!r.rows[0]?.ok;
  }

  async releaseHeartbeatLock() {
    await this.client.query(`select release_lock($1,$2)`, ['heartbeat', this.agentId]);
  }

  async updateAgentState(state) {
    await this.client.query(
      `insert into agent_state(agent_id, updated_ts, json_state)
       values($1, now(), $2)
       on conflict (agent_id) do update set updated_ts=now(), json_state=excluded.json_state`,
      [this.agentId, state]
    );
  }

  async updateHeartbeat(intervalSec, status = 'running') {
    await this.client.query(
      `insert into agents(agent_id, status, last_seen_ts, heartbeat_interval_sec)
       values($1,$2,now(),$3)
       on conflict (agent_id) do update set status=excluded.status, last_seen_ts=now(), heartbeat_interval_sec=excluded.heartbeat_interval_sec`,
      [this.agentId, status, intervalSec]
    );
  }

  async tick() {
    await this.updateHeartbeat(60, 'running');
    const lockOk = await this.acquireHeartbeatLock(120);
    if (!lockOk) {
      await this.logHealth('warning', 'heartbeat', 'lock busy; skipping tick');
      return { hadWork: false, reason: 'lock_busy' };
    }

    let hadWork = false;
    try {
      const job = await this.claimNextJob();
      if (job) {
        hadWork = true;
        try {
          // Placeholder job executor
          await this.appendMemory('job_queue', 'decision', `Executing job ${job.id}:${job.job_type}`, { payload: job.payload });
          await this.completeJob(job.id);
          await this.logHealth('info', 'job_queue', 'job completed', { job_id: job.id, type: job.job_type });
        } catch (e) {
          await this.failJob(job.id, e.message);
          await this.logHealth('error', 'job_queue', 'job failed', { job_id: job.id, error: e.message });
        }
      } else {
        const resurfaced = await this.resurfaceOverdueTasks();
        if (resurfaced.length) {
          hadWork = true;
          await this.enqueueJob('review_resurfaced_tasks', { ids: resurfaced.map(t=>t.id) }, 2, 3);
        }
      }

      const loops = await this.openLoopsSummary();
      await this.updateAgentState({ last_tick: nowIso(), hadWork, open_loops_counts: {
        blocked: loops.blocked.length,
        overdue: loops.overdue.length,
        unreviewed_7d: loops.unreviewed_7d.length,
      }});

      if (loops.blocked.length) {
        await this.logHealth('warning', 'open_loops', 'blocked tasks require user input', { blocked: loops.blocked.slice(0,5) });
      }

      await this.logHealth('info', 'heartbeat', 'tick complete', { hadWork });
      return { hadWork, loops };
    } finally {
      await this.releaseHeartbeatLock();
    }
  }

  async runInternalLoop(maxTicks = 0) {
    let interval = 30; // sec
    let tickCount = 0;
    while (true) {
      const r = await this.tick();
      interval = r.hadWork ? 20 : Math.min(600, Math.floor(interval * 1.6));
      await this.updateHeartbeat(interval, 'running');
      tickCount++;
      if (maxTicks > 0 && tickCount >= maxTicks) break;
      await sleep(interval * 1000);
    }
  }

  async weeklyReview() {
    const done = await this.client.query(`select count(*)::int as n from tasks where coalesce(status,'')='done'`);
    const fail = await this.client.query(`select count(*)::int as n from health_events where level in ('error','critical') and ts > now()-interval '7 days'`);
    const blocked = await this.client.query(`select count(*)::int as n from tasks where coalesce(status,'')='blocked'`);

    const completion = done.rows[0]?.n || 0;
    const failures = fail.rows[0]?.n || 0;
    const blockedCount = blocked.rows[0]?.n || 0;

    const content = `Weekly review: completed=${completion}, failures=${failures}, blocked=${blockedCount}`;
    const decisions = {
      suggested_upgrades: [
        blockedCount > 0 ? 'Improve blocker escalation prompts' : 'Maintain current blocker policy',
        failures > 5 ? 'Increase retry/backoff and circuit-breaker checks' : 'Keep retry policy',
      ],
    };

    await this.client.query(
      `insert into reflections(period, content, decisions) values('weekly',$1,$2)`,
      [content, decisions]
    );

    if (failures > 5 || blockedCount > 0) {
      await this.createTask('Weekly architecture improvement', content, 2, null, 'weekly');
    }

    return { completion, failures, blocked: blockedCount, decisions };
  }
}

async function main() {
  const cmd = process.argv[2] || 'help';
  const brain = new AgentBrain({ agentId: process.env.AGENT_ID || 'ANIMAL' });
  await brain.connect();

  try {
    if (cmd === 'phase1') {
      // connectivity first (cannot continue if down)
      const ok = await brain.validateConnectivity();
      if (!ok.ok) process.exit(2);
      await brain.applyMigrations();
      // re-log connectivity now that health_events table is guaranteed
      await brain.validateConnectivity();
      console.log('PHASE1_PASS');
      return;
    }
    if (cmd === 'boot') {
      const r = await brain.bootHydrate();
      console.log(JSON.stringify(r, null, 2));
      return;
    }
    if (cmd === 'tick') {
      const r = await brain.tick();
      console.log(JSON.stringify(r, null, 2));
      return;
    }
    if (cmd === 'loop') {
      const maxTicks = Number(process.argv[3] || 0);
      await brain.runInternalLoop(maxTicks);
      return;
    }
    if (cmd === 'weekly-review') {
      const r = await brain.weeklyReview();
      console.log(JSON.stringify(r, null, 2));
      return;
    }

    if (cmd === 'create-task') {
      await brain.createTask(process.argv[3] || 'Untitled task', process.argv[4] || '', Number(process.argv[5] || 3), process.argv[6] || null, process.argv[7] || null);
      console.log('TASK_CREATED');
      return;
    }
    if (cmd === 'complete-task') {
      await brain.completeTask(process.argv[3]);
      console.log('TASK_COMPLETED');
      return;
    }
    if (cmd === 'block-task') {
      await brain.blockTask(process.argv[3], process.argv.slice(4).join(' ') || 'blocked');
      console.log('TASK_BLOCKED');
      return;
    }
    if (cmd === 'resurface') {
      const r = await brain.resurfaceOverdueTasks();
      console.log(JSON.stringify({count:r.length, tasks:r}, null, 2));
      return;
    }
    if (cmd === 'register-skill') {
      await brain.registerSkill(process.argv[3], process.argv[4] || '', Number(process.argv[5] || 3), process.argv[6] || null);
      console.log('SKILL_REGISTERED');
      return;
    }
    if (cmd === 'skill-outcome') {
      await brain.recordSkillOutcome(process.argv[3], process.argv[4], String(process.argv[5]||'true')==='true', Number(process.argv[6]||0));
      console.log('SKILL_OUTCOME_RECORDED');
      return;
    }
    if (cmd === 'route') {
      const r = await brain.routingDecision(process.argv.slice(3).join(' '));
      console.log(JSON.stringify(r, null, 2));
      return;
    }

    if (cmd === 'smoke') {
      await brain.validateConnectivity();
      await brain.appendMemory('smoke', 'fact', 'smoke event');
      await brain.createTask('Smoke task', 'task engine check', 3);
      await brain.enqueueJob('smoke_job', { x: 1 }, 3, 2);
      const t = await brain.tick();
      console.log(JSON.stringify({ ok: true, tick: t }, null, 2));
      return;
    }

    console.log('Usage: agent_brain_v2.js phase1|boot|tick|loop [maxTicks]|weekly-review|smoke|create-task|complete-task|block-task|resurface|register-skill|skill-outcome|route');
  } finally {
    await brain.close();
  }
}

main().catch(async (e) => {
  console.error('FATAL', e.message);
  process.exit(1);
});
