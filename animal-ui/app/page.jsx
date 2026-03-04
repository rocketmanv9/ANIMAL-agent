'use client';

import { useEffect, useState } from 'react';
import Panel from './components/Panel';

export default function Home() {
  const [data, setData] = useState(null);
  const [chatText, setChatText] = useState('');
  const [chatReply, setChatReply] = useState('');
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    const r = await fetch('/api/dashboard');
    const j = await r.json();
    setData(j);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function sendChat(e) {
    e.preventDefault();
    if (!chatText.trim()) return;
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ message: chatText })
    });
    const j = await r.json();
    setChatReply(j.reply || j.error || 'done');
    setChatText('');
    load();
  }

  async function proposeTool(tool, mode) {
    await fetch('/api/tool-action', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ tool, mode, payload: {} })
    });
    load();
  }

  return (
    <main style={{ padding: 14, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ margin: '8px 0 14px 0' }}>ANIMAL Command Center</h1>
      <p style={{ marginTop: 0, color: '#b6c2f5' }}>
        Tools, open loops, health, and direct Clawbot requests.
      </p>

      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit,minmax(300px,1fr))' }}>
        <Panel title="Chat Clawbot">
          <form onSubmit={sendChat} style={{ display: 'flex', gap: 8 }}>
            <input
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              placeholder="Tell ANIMAL what to do..."
              style={{ flex: 1, padding: 10, borderRadius: 8, border: '1px solid #3a4a7a', background: '#0d1430', color: '#fff' }}
            />
            <button style={{ padding: '10px 14px', borderRadius: 8, background: '#2f5cff', color: '#fff', border: 0 }}>Send</button>
          </form>
          {chatReply && <p style={{ marginTop: 10, color: '#9de6b5' }}>{chatReply}</p>}
        </Panel>

        <Panel title="Open Loops">
          {!data?.ok && <p>{loading ? 'Loading...' : 'Error loading open loops'}</p>}
          {data?.ok && (
            <>
              <div>Blocked: <b>{data.openLoops.blocked.length}</b></div>
              <div>Overdue: <b>{data.openLoops.overdue.length}</b></div>
              <div>Unreviewed &gt;7d: <b>{data.openLoops.unreviewed7d.length}</b></div>
            </>
          )}
        </Panel>

        <Panel title="Agent Heartbeat">
          {data?.agents?.length ? data.agents.map((a) => (
            <div key={a.agent_id} style={{ marginBottom: 8 }}>
              <div><b>{a.agent_id}</b> — {a.status}</div>
              <div style={{ color: '#9db2ff', fontSize: 12 }}>last_seen: {a.last_seen_ts}</div>
            </div>
          )) : <p>No agent rows yet.</p>}
        </Panel>
      </div>

      <div style={{ marginTop: 12, display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))' }}>
        <Panel title="Tools Registry">
          <div style={{ maxHeight: 320, overflow: 'auto' }}>
            {(data?.tools || []).map((t) => (
              <div key={t.skill_name} style={{ borderBottom: '1px solid #27335f', padding: '8px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <b>{t.skill_name}</b>
                  <span style={{ fontSize: 12, color: '#9db2ff' }}>rank {t.complexity_rank}</span>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                  <button onClick={() => proposeTool(t.skill_name, 'propose')} style={{ padding: '6px 8px', borderRadius: 6 }}>Propose</button>
                  <button onClick={() => proposeTool(t.skill_name, 'execute')} style={{ padding: '6px 8px', borderRadius: 6 }}>Execute</button>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Health Events">
          <div style={{ maxHeight: 320, overflow: 'auto', fontSize: 13 }}>
            {(data?.health || []).map((h, i) => (
              <div key={i} style={{ borderBottom: '1px solid #27335f', padding: '6px 0' }}>
                <div><b>{h.level}</b> — {h.component}</div>
                <div>{h.message}</div>
                <div style={{ color: '#9db2ff' }}>{h.ts}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div style={{ marginTop: 12 }}>
        <button onClick={load} style={{ padding: '10px 14px', borderRadius: 8 }}>Refresh</button>
      </div>
    </main>
  );
}
