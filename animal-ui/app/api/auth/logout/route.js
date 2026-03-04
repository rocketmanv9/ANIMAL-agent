import { cookies } from 'next/headers';

export async function POST() {
  const jar = cookies();
  jar.set('animal_session', '', { httpOnly: true, secure: true, sameSite: 'lax', path: '/', maxAge: 0 });
  return Response.json({ ok: true });
}
