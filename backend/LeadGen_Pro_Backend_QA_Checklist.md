# LeadGen Pro Backend QA Checklist

**Purpose:** Final backend verification checklist before frontend integration and production deployment.  
**Status:** Backend is feature-complete for beta/MVP. Complete these checks before production.

---

## A. Repository Cleanup

- [ ] Remove real `.env` from repo/package.
- [ ] Keep only `.env.example` with placeholder values.
- [ ] Remove `venv/` from repo/package.
- [ ] Remove all `__pycache__/` folders.
- [ ] Remove all `*.pyc` files.
- [ ] Remove `.pytest_cache/`.
- [ ] Remove runtime logs: `logs/`, `scraper.log`, `*.log`.
- [ ] Remove export files from `media/exports/`.
- [ ] Remove `celerybeat-schedule.*` files.
- [ ] Remove old/backup code files unless intentionally needed:
  - [ ] `config/settings_old.py`
  - [ ] `apps/services/scraper/engine_updated.py`
  - [ ] `apps/services/scraper/engine_complete_updated.py`
- [ ] Confirm `.gitignore` blocks all runtime/generated files.

---

## B. Dependency / Requirements QA

- [ ] Update `requirements.txt` with all packages currently used:
  - [ ] `channels`
  - [ ] `channels-redis`
  - [ ] `daphne`
  - [ ] `django-cors-headers`
  - [ ] `drf-spectacular`
  - [ ] `whitenoise`
  - [ ] `django-ratelimit`
  - [ ] `google-genai`
  - [ ] `openpyxl`
  - [ ] `sentry-sdk`
  - [ ] `factory-boy`
  - [ ] `pytest`
  - [ ] `pytest-django`
- [ ] Run fresh environment install:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m playwright install chromium
```

- [ ] Confirm `python manage.py check` passes on fresh environment.

---

## C. Environment QA

- [ ] `.env.example` includes all required variables.
- [ ] `DJANGO_SECRET_KEY` is changed in production.
- [ ] `DEBUG=False` in production.
- [ ] `DJANGO_ALLOWED_HOSTS` set correctly.
- [ ] `CORS_ALLOWED_ORIGINS` includes frontend URL.
- [ ] `CSRF_TRUSTED_ORIGINS` includes frontend URL.
- [ ] `POSTGRES_*` values configured.
- [ ] `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` configured.
- [ ] `GEMINI_API_KEY` configured if AI is enabled.
- [ ] `SENTRY_DSN` configured for production monitoring.

---

## D. Database / Migration QA

Run:

```bash
python manage.py makemigrations --check
python manage.py migrate
python manage.py check
```

- [ ] No pending model changes.
- [ ] All migrations apply successfully.
- [ ] Superuser can be created.
- [ ] Admin panel opens.

---

## E. Auth QA

- [ ] Register user works.
- [ ] Login works.
- [ ] JWT access token works.
- [ ] JWT refresh works.
- [ ] Protected API without token returns `401`.
- [ ] Normal user cannot access another user's searches/leads.
- [ ] Staff/superuser can access admin dashboard APIs.
- [ ] Non-staff user receives `403` for admin dashboard APIs.

---

## F. Search / Scraper QA

- [ ] Create search API works.
- [ ] Search creates `SearchQueryTask` rows.
- [ ] Celery receives search task.
- [ ] Playwright opens Chromium successfully.
- [ ] Google Maps search opens.
- [ ] Leads are scraped and saved.
- [ ] Duplicate leads are skipped/updated safely.
- [ ] Search progress updates.
- [ ] Search completes successfully.
- [ ] Search failure logs monitoring event.
- [ ] Pause/resume/cancel tested if used in frontend.

Test:

```json
{
  "keywords": ["plumber"],
  "locations": ["Perth"],
  "max_leads": 5,
  "scrape_mode": "safe",
  "email_enrichment": true
}
```

---

## G. Lead Management QA

- [ ] Leads list API returns only current user's leads.
- [ ] Pagination works.
- [ ] Search filters work:
  - [ ] `search_id`
  - [ ] `keyword`
  - [ ] `location`
  - [ ] `status`
  - [ ] `rating`
  - [ ] `has_email`
  - [ ] `has_website`
  - [ ] `website_status`
  - [ ] `enrichment_status`
  - [ ] `min_score`
- [ ] Lead update works for notes/status/favorite/tags.
- [ ] Bulk actions work.
- [ ] Lead lists work.

---

## H. Enrichment QA

- [ ] Single lead website enrichment works.
- [ ] Bulk enrichment works.
- [ ] Search enrichment works.
- [ ] Website status values are saved.
- [ ] Broken/404/expired/timeout/SSL/protected statuses tested.
- [ ] Social-only and free-builder detection works.
- [ ] Email extraction works where email exists.
- [ ] Email source pages saved.
- [ ] Email confidence saved.
- [ ] Enrichment job progress updates.
- [ ] Failed enrichment creates monitoring event.

---

## I. Export QA

### Direct CSV Export

```http
GET /api/leads/export/?search_id=1&include_ai=true
```

- [ ] Direct CSV export returns `200`.
- [ ] CSV downloads correctly.
- [ ] AI columns appear when `include_ai=true`.
- [ ] AI columns are blank, not broken, when lead has no AI insight.

### Background Export

```http
POST /api/leads/exports/
```

Body:

```json
{
  "export_type": "xlsx",
  "search_id": 1,
  "include_ai": true
}
```

- [ ] Background export returns `202`.
- [ ] Celery generates file.
- [ ] Export history shows completed status.
- [ ] Download endpoint works.
- [ ] CSV export works.
- [ ] XLSX export works.
- [ ] Selected leads export works.
- [ ] Lead list export works.
- [ ] Export file cleanup works.

---

## J. Realtime QA

Connect frontend/browser:

```text
ws://127.0.0.1:8000/ws/realtime/?token=ACCESS_TOKEN
```

- [ ] WebSocket connects.
- [ ] `connected` event received.
- [ ] Realtime test event received.
- [ ] `search_progress` received during scraping.
- [ ] `lead_found` received when lead saves.
- [ ] `enrichment_progress` received.
- [ ] `lead_enriched` received.
- [ ] `export_started` received.
- [ ] `export_completed` received.
- [ ] `ai_job_progress` received.
- [ ] `ai_lead_completed` received.

---

## K. AI QA

- [ ] `GET /api/ai/usage/` works.
- [ ] Gemini API key works.
- [ ] Single lead AI insight works.
- [ ] Custom target offer works.
- [ ] Custom campaign goal works.
- [ ] Custom tone works.
- [ ] Custom outreach channel works.
- [ ] AI output is clean text without `\n\n` line breaks.
- [ ] AI usage credits are logged.
- [ ] Bulk AI job works.
- [ ] AI job finalizer marks jobs completed.
- [ ] Failed AI call creates monitoring event.
- [ ] AI fields export correctly.

Example:

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

---

## L. Admin Dashboard QA

Use staff/superuser token.

- [ ] Overview API works.
- [ ] Users list works.
- [ ] User detail works.
- [ ] Usage update works.
- [ ] Suspend user works.
- [ ] Activate user works.
- [ ] Search monitoring works.
- [ ] Lead monitoring works.
- [ ] Export monitoring works.
- [ ] Enrichment job monitoring works.
- [ ] System health API works.
- [ ] Failure summary works.

---

## M. Monitoring QA

- [ ] `GET /api/monitoring/health/` works.
- [ ] DB health shows `ok`.
- [ ] Redis health shows `ok`.
- [ ] Celery health shows `ok` when worker is running.
- [ ] Test event creates SystemEvent.
- [ ] Events list works.
- [ ] Resolve/unresolve works.
- [ ] Failed scraper task logs event.
- [ ] Failed export logs event.
- [ ] Failed enrichment logs event.
- [ ] Failed AI logs event.
- [ ] Sentry configured in production if needed.

---

## N. Performance / Worker QA

Local Windows can use:

```bash
python -m celery -A config worker --pool=solo --loglevel=info
```

Production should use separate workers/queues later:

```bash
celery -A config worker -Q scraper --loglevel=info
celery -A config worker -Q enrichment,export,ai,cleanup --loglevel=info
celery -A config beat --loglevel=info
```

- [ ] Long scraper task does not block all other jobs in production setup.
- [ ] Export job works while scraper runs.
- [ ] AI job works while scraper runs.
- [ ] Cleanup job runs daily.

---

## O. Security QA

- [ ] `.env` not committed.
- [ ] Production `DEBUG=False`.
- [ ] Production secret key changed.
- [ ] Admin endpoints staff-only.
- [ ] User data isolated by authenticated user.
- [ ] Export download checks owner.
- [ ] Lead update checks owner.
- [ ] AI insight checks owner.
- [ ] Search detail checks owner.
- [ ] CORS locked to frontend domain.
- [ ] CSRF trusted origins configured.
- [ ] HTTPS enabled in production.
- [ ] Sentry does not send sensitive PII unnecessarily.

---

## P. Production Deployment QA

- [ ] PostgreSQL production database configured.
- [ ] Redis 7+ configured.
- [ ] Daphne/ASGI service configured.
- [ ] Celery worker service configured.
- [ ] Celery beat service configured.
- [ ] Nginx reverse proxy configured.
- [ ] Static files collected.
- [ ] Media/export storage configured.
- [ ] Logs directory writable.
- [ ] Playwright Chromium installed on server.
- [ ] Headless Playwright works on server.
- [ ] Health endpoint returns success.
- [ ] Background task worker survives restart.

---

## Final Readiness Decision

Frontend can start when:

- [ ] API docs available at `/api/docs/`.
- [ ] Auth flow confirmed.
- [ ] Search flow confirmed.
- [ ] Leads list confirmed.
- [ ] Export flow confirmed.
- [ ] WebSocket confirmed.
- [ ] AI insight confirmed.
- [ ] Admin dashboard endpoints confirmed.

Production launch can start when:

- [ ] All repository cleanup is complete.
- [ ] Requirements are complete.
- [ ] Fresh install passes.
- [ ] QA tests pass.
- [ ] Deployment hardening is complete.
