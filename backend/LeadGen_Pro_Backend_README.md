# LeadGen Pro Backend README

**Project:** LeadGen Pro Backend  
**Stack:** Django 5.2, Django REST Framework, PostgreSQL, Redis, Celery, Playwright, Django Channels, Gemini AI  
**Status:** Feature-complete for beta/MVP backend. Ready to start frontend integration after the cleanup checklist below.

---

## 1. What This Backend Does

LeadGen Pro is a lead generation SaaS backend that can:

- Register/login users with JWT authentication.
- Create Google Maps scraping searches.
- Scrape Google Maps leads using Playwright.
- Save leads in real time.
- Enrich leads with website status, email extraction, social links, website platform, and opportunity scoring.
- Support usage limits for searches, leads, exports, and AI.
- Export leads as CSV/XLSX, including optional AI fields.
- Provide realtime WebSocket events for search progress, lead found, enrichment, exports, and AI jobs.
- Provide admin dashboard APIs.
- Provide monitoring/error tracking APIs and system events.
- Generate AI lead insights and outreach copy using Gemini.

---

## 2. Main Apps

```text
apps/accounts          User auth, JWT, registration, login, verification
apps/searches          Search creation, query tasks, pause/resume/cancel support
apps/leads             Lead models, lead lists, exports, enrichment jobs
apps/services          Scraper, browser, parser, email extractor, website checker
apps/usage             Free/beta usage limits and usage counters
apps/realtime          Django Channels WebSocket layer
apps/admin_dashboard   Custom admin dashboard backend APIs
apps/monitoring        System health, event logs, task/error tracking
apps/ai                Gemini AI insights, AI jobs, AI usage logs
apps/core              Shared health/error/rate-limit helpers
```

---

## 3. Important Features Completed

### Core SaaS Backend

- Custom user model
- JWT authentication
- Rate limiting
- User-specific data access
- Usage limits
- Beta/free usage support

### Scraping

- Google Maps search scraping
- Playwright browser control
- Search query task tracking
- Pause/resume/cancel foundation
- Duplicate handling
- Lead save safety
- Per-user ownership

### Lead Enrichment

- Website status checker
- DNS/domain status checks
- Broken website detection
- 404/timeout/SSL/redirect/protected detection
- Social-only website detection
- Free website builder detection
- Platform detection
- Email extraction
- Email source pages
- Email confidence
- Lead scoring and opportunity reason

### Export System

- Direct CSV export
- Background CSV export
- Background XLSX export
- Export history
- Export download endpoint
- Export cleanup support
- Selected leads export
- Search leads export
- Lead list export
- Optional AI fields inside export using `include_ai=true`

### Realtime

- Django Channels + Redis channel layer
- JWT-authenticated WebSocket connection
- User-specific realtime groups
- Realtime test endpoint
- Search progress events
- Lead found events
- Enrichment progress events
- Export status events
- AI job progress events

### Admin Dashboard Backend

- Admin overview
- User list/detail
- User usage update
- Suspend/activate user
- Search monitoring
- Lead monitoring
- Export monitoring
- Enrichment job monitoring
- System health/failure overview

### Monitoring

- SystemEvent model
- API for health checks
- API for monitoring events
- Resolve/unresolve monitoring events
- Celery health check
- Redis health check
- DB health check
- Task failure logging
- Sentry-ready production config

### AI / Gemini

- Gemini API integration
- Single lead AI insight generation
- Custom campaign goal support
- Custom target offer support
- Custom tone/audience/channel support
- AI cold email
- AI first line
- AI follow-ups
- AI Facebook/WhatsApp messages
- AI website weakness
- AI local SEO opportunity
- AI credit tracking
- Bulk AI jobs
- Realtime AI progress events

---

## 4. Required Services

For local development:

```text
PostgreSQL
Redis 7+
Python 3.11+
Playwright Chromium
Celery worker
Celery beat
Django ASGI/Daphne server
```

Recommended local startup:

```bash
python manage.py runserver
python -m celery -A config worker --pool=solo --loglevel=info
python -m celery -A config beat --loglevel=info
```

Install Playwright browser:

```bash
python -m playwright install chromium
```

---

## 5. Environment Variables

Create `.env` from `.env.example`.

Important variables:

```env
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=change-me
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173

POSTGRES_DB=leadgen_saas_db
POSTGRES_USER=leadgen_user
POSTGRES_PASSWORD=change-me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_URL=redis://127.0.0.1:6380/0
CELERY_BROKER_URL=redis://127.0.0.1:6380/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6380/0

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

REALTIME_ENABLED=true

AI_ENABLED=true
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
AI_BULK_MAX_LEADS=50
AI_DEFAULT_MONTHLY_CREDITS=500
AI_COST_LEAD_INSIGHT=3
AI_COST_FULL_PERSONALIZATION=5
```

Never commit real `.env` values to Git.

---

## 6. Requirements File Must Be Updated

The uploaded ZIP has a `requirements.txt`, but it is missing several packages used by the current backend code.

Recommended minimum `requirements.txt` additions:

```txt
channels
channels-redis
daphne
django-cors-headers
drf-spectacular
whitenoise
django-ratelimit
google-genai
openpyxl
sentry-sdk
factory-boy
pytest
pytest-django
```

The current file already contains core items like Django, DRF, Celery, Redis, Playwright, Requests, BeautifulSoup, PostgreSQL driver, and SimpleJWT.

Before installing on a fresh machine, update `requirements.txt` and run:

```bash
pip install -r requirements.txt
```

---

## 7. Database Setup

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
```

Create admin user:

```bash
python manage.py createsuperuser
```

---

## 8. Core API Routes

### Health and Docs

```http
GET /api/health/
GET /api/schema/
GET /api/docs/
GET /api/redoc/
```

### Auth

```http
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/token/refresh/
POST /api/auth/token/verify/
```

### Searches

```http
GET  /api/searches/
POST /api/searches/
GET  /api/searches/<id>/
POST /api/searches/<id>/pause/
POST /api/searches/<id>/resume/
POST /api/searches/<id>/cancel/
```

### Leads

```http
GET   /api/leads/
PATCH /api/leads/<lead_id>/
POST  /api/leads/bulk-action/
```

### Exports

Direct CSV:

```http
GET /api/leads/export/?search_id=1&include_ai=true
```

Background export:

```http
POST /api/leads/exports/
GET  /api/leads/export-history/
GET  /api/leads/exports/<export_id>/
GET  /api/leads/exports/<export_id>/download/
DELETE /api/leads/exports/<export_id>/delete/
```

Body example:

```json
{
  "export_type": "xlsx",
  "search_id": 1,
  "include_ai": true
}
```

### Enrichment

```http
POST /api/leads/<lead_id>/enrich-website/
POST /api/leads/bulk-enrich-website/
POST /api/leads/search/<search_id>/enrich-website/
GET  /api/leads/enrichment-jobs/
```

### AI

```http
GET  /api/ai/usage/
POST /api/ai/leads/<lead_id>/insight/
GET  /api/ai/leads/<lead_id>/insight/
POST /api/ai/bulk-generate/
GET  /api/ai/jobs/
GET  /api/ai/jobs/<job_id>/
```

Custom AI insight body:

```json
{
  "force": true,
  "target_offer": "Web development and AI automation",
  "campaign_goal": "Pitch plumbers who may need a better website and more calls from Google",
  "tone": "friendly, simple, not too salesy",
  "target_audience": "local plumbing business owner",
  "outreach_channel": "email",
  "custom_instructions": "Keep email short. Do not mention a 15-minute call."
}
```

### Realtime

```text
ws://127.0.0.1:8000/ws/realtime/?token=ACCESS_TOKEN
```

Test event:

```http
POST /api/leads/realtime/test/
```

### Admin Dashboard

Requires staff/superuser token.

```http
GET /api/admin-dashboard/overview/
GET /api/admin-dashboard/users/
GET /api/admin-dashboard/users/<user_id>/
PATCH /api/admin-dashboard/users/<user_id>/usage/
POST /api/admin-dashboard/users/<user_id>/suspend/
POST /api/admin-dashboard/users/<user_id>/activate/
GET /api/admin-dashboard/searches/
GET /api/admin-dashboard/leads/
GET /api/admin-dashboard/exports/
GET /api/admin-dashboard/enrichment-jobs/
GET /api/admin-dashboard/system-health/
GET /api/admin-dashboard/failures/
```

### Monitoring

Requires staff/superuser token.

```http
GET  /api/monitoring/health/
GET  /api/monitoring/events/
GET  /api/monitoring/events/<event_id>/
POST /api/monitoring/events/<event_id>/resolve/
POST /api/monitoring/events/<event_id>/unresolve/
POST /api/monitoring/test-event/
```

---

## 9. Realtime Event Types

Frontend should handle:

```text
connected
notification
search_started
search_progress
search_completed
search_failed
lead_found
enrichment_started
enrichment_progress
lead_enriched
export_started
export_completed
export_failed
ai_job_started
ai_job_progress
ai_lead_completed
ai_job_completed
ai_job_failed
```

---

## 10. Frontend Integration Notes

Start frontend after confirming:

- Login returns access/refresh tokens.
- Authenticated requests use `Authorization: Bearer <access_token>`.
- WebSocket connects with `?token=<access_token>`.
- Search creation returns a search ID.
- Leads list supports pagination and filters.
- Export job returns `202` and later `download_url`.
- AI insight endpoint works for one lead.
- Admin dashboard requires staff/superuser token.

---

## 11. Important Cleanup Before Git/Frontend Handoff

The uploaded ZIP contains generated/runtime files that should not be committed or shared as the clean backend repo:

```text
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
logs/
media/exports/
celerybeat-schedule.*
scraper.log
config/settings_old.py
apps/services/scraper/engine_updated.py
apps/services/scraper/engine_complete_updated.py
```

Keep `.env.example`, but remove real `.env` from the repo.

Recommended `.gitignore` additions:

```gitignore
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
logs/
media/exports/
celerybeat-schedule.*
*.log
```

---

## 12. Current Backend Readiness

```text
Feature development: Complete for beta/MVP
Frontend integration: Ready after requirements cleanup
Production deployment: Needs deployment hardening
Payment/subscription: Planned later
```

The backend is ready to start frontend integration, but before production deployment, complete the QA checklist.
