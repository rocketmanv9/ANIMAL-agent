import { getDb } from '@/lib/db';

export async function POST(req) {
  try {
    const { tool, mode = 'propose', payload = {} } = await req.json();
    if (!tool) return Response.json({ ok: false, error: 'tool required' }, { status: 400 });

    const db = getDb();

    if (mode === 'execute') {
      await db.query(
        `insert into job_queue(job_type,payload,priority,max_attempts,status,available_at)
         values('tool_execute',$1,2,5,'queued',now())`,
        [{ tool, payload }]
      );
      return Response.json({ ok: true, queued: true, mode: 'execute' });
    }

    await db.query(
      `insert into tasks(status,priority,title,description,metadata,last_review_ts)
       values('todo',2,$1,$2,$3,now())`,
      [
        `Tool proposal: ${tool}`,
        `Proposed tool action for review`,
        { kind: 'tool_proposal', tool, payload }
      ]
    );

    return Response.json({ ok: true, queued: false, mode: 'propose' });
  } catch (e) {
    return Response.json({ ok: false, error: e.message }, { status: 500 });
  }
}
