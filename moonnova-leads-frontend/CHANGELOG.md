# MoonNova Leads Frontend - Professional SaaS Update

## Completed

- Rebuilt the dashboard shell with a premium dark/gold/teal SaaS theme.
- Fixed sidebar layout so the user card and logout stay inside the visible screen.
- Added collapsible desktop sidebar and improved mobile drawer behavior.
- Updated global card, table, button, input, loading, and badge styling.
- Connected dashboard stats with backend searches, lead count, and usage data.
- Rebuilt Searches page with task estimation, templates, progress bars, empty state, and professional table layout.
- Rebuilt Leads page with stronger filters, stats cards, bulk actions, responsive table, loading state, empty state, pagination, and lead drawer support.
- Rebuilt Usage page to map with `/api/usage/me/`.
- Rebuilt Settings page with profile, security, workflow defaults, and developer config.
- Added frontend email verification token handling for `/verify-email/:token` and `/auth/verify-email/:token`.
- Added resend verification flow on register/login.
- Added user-facing note about Google Password Manager breach warning.
- Fixed backend lead filter mapping: frontend `search` now maps to backend `q`, `broken_website` maps to `is_broken_website`, etc.
- Confirmed production build passes.

## Backend note

Email sending is controlled by Django backend SMTP settings, not frontend code. To send verification emails, configure:

- `FRONTEND_URL=http://localhost:5173`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS=True`

Also update backend email template wording from `LeadGen Pro` to `MoonNova Leads`.
