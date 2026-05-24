# MoonNova Leads Frontend

Professional React + Vite + TypeScript frontend for MoonNova Leads.

## Start

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Environment

Create `.env.local`:

```env
VITE_API_URL=http://127.0.0.1:8000/api
VITE_WS_URL=ws://127.0.0.1:8000/ws/realtime/
```

## Email verification

The frontend supports verification routes:

- `/verify-email/:token`
- `/auth/verify-email/:token`

The backend must send this frontend URL in the verification email. Configure Django `FRONTEND_URL` and SMTP settings.

## Browser password warning

If Chrome shows “Change your password”, this warning is from Google Password Manager because the test password was reused or found in breach databases. Use a unique password for testing.
