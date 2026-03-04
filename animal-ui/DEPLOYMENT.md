# ANIMAL UI Deployment (Vercel)

## Fix 404 NOT_FOUND
Use one of these (recommended first):

### Option A (recommended)
In Vercel Project Settings:
- Root Directory: `animal-ui`
- Framework Preset: `Next.js`

### Option B
Use repo root with `vercel.json` (already added), which builds `animal-ui`.

## Required Environment Variables
Set in Vercel project:
- `DATABASE_URL`
- `ANIMAL_UI_EMAIL` (your email, exact)
- `ANIMAL_UI_PASSCODE` (strong passcode)

## Auth behavior
- All routes protected by middleware
- Only `/login` and auth routes are public
- Login requires matching `ANIMAL_UI_EMAIL` + `ANIMAL_UI_PASSCODE`

## Local smoke test
```bash
cd animal-ui
npm install
ANIMAL_UI_EMAIL=grant.m.anderson2021@gmail.com ANIMAL_UI_PASSCODE=changeme DATABASE_URL="..." npm run build
npm run dev
```

Open:
- `/login` (must authenticate)
- `/` dashboard after login
