import { cookies } from 'next/headers';

export async function POST(req) {
  try {
    const { email, passcode } = await req.json();

    const allowEmail = (process.env.ANIMAL_UI_EMAIL || '').toLowerCase().trim();
    const allowPass = process.env.ANIMAL_UI_PASSCODE || '';

    if (!allowEmail || !allowPass) {
      return Response.json({ ok: false, error: 'Server auth not configured' }, { status: 500 });
    }

    if (!email || !passcode) {
      return Response.json({ ok: false, error: 'Missing email/passcode' }, { status: 400 });
    }

    if (String(email).toLowerCase().trim() !== allowEmail || String(passcode) !== allowPass) {
      return Response.json({ ok: false, error: 'Invalid credentials' }, { status: 401 });
    }

    const jar = cookies();
    jar.set('animal_session', 'ok', {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 12,
    });

    return Response.json({ ok: true });
  } catch (e) {
    return Response.json({ ok: false, error: e.message }, { status: 500 });
  }
}
