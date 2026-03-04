'use client';

import { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [passcode, setPasscode] = useState('');
  const [err, setErr] = useState('');

  async function onSubmit(e) {
    e.preventDefault();
    setErr('');
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email, passcode }),
    });
    const j = await res.json();
    if (!res.ok || !j.ok) {
      setErr(j.error || 'Login failed');
      return;
    }
    window.location.href = '/';
  }

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <form
        onSubmit={onSubmit}
        style={{ width: '100%', maxWidth: 420, background: '#121a33', border: '1px solid #2a3765', borderRadius: 14, padding: 18 }}
      >
        <h1 style={{ marginTop: 0 }}>ANIMAL Login</h1>
        <p style={{ color: '#9db2ff' }}>Restricted access: only approved user.</p>

        <label style={{ display: 'block', marginTop: 10, fontSize: 13 }}>Email</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 8, border: '1px solid #3a4a7a', background: '#0d1430', color: '#fff' }}
        />

        <label style={{ display: 'block', marginTop: 10, fontSize: 13 }}>Passcode</label>
        <input
          type="password"
          value={passcode}
          onChange={(e) => setPasscode(e.target.value)}
          style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 8, border: '1px solid #3a4a7a', background: '#0d1430', color: '#fff' }}
        />

        {err && <p style={{ color: '#ff8f8f' }}>{err}</p>}

        <button
          style={{ marginTop: 14, width: '100%', padding: 10, borderRadius: 8, border: 0, background: '#2f5cff', color: '#fff' }}
        >
          Sign in
        </button>
      </form>
    </main>
  );
}
