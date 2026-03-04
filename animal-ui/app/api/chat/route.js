import { getDb } from '@/lib/db';

export async function POST(req) {
  try {
    const { message } = await req.json();
    if (!message || !String(message).trim()) {
      return Response.json({ ok: false, error: 'message required' }, { status: 400 });
    }

    const db = getDb();

    // Store incoming message as memory + actionable task for Clawbot loop
    await db.query(
      `insert into memory_events(agent_id, source, type, content, tags)
       values($1,$2,$3,$4,$5)`,
      ['ANIMAL', 'ui_chat', 'fact', String(message), { channel: 'animal_ui' }]
    );

    await db.query(
      `insert into tasks(status,priority,title,description,metadata,last_review_ts)
       values('todo',2,$1,$2,$3,now())`,
      ['UI chat request', String(message), { kind: 'ui_chat_request', requires_user: false }]
    );

    return Response.json({
      ok: true,
      reply:
        'Message received by ANIMAL. Request logged to memory_events + tasks for processing in heartbeat loop.'
    });
  } catch (e) {
    return Response.json({ ok: false, error: e.message }, { status: 500 });
  }
}
