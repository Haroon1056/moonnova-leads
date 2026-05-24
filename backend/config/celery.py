import os
import sys
import asyncio

from celery import Celery
from kombu import Queue

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.dev",
)

app = Celery("config")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

# =====================================================
# PROFESSIONAL QUEUE SETUP
# =====================================================
# scraping   = Google Maps scraping jobs
# enrichment = website checker + email enrichment jobs
# default    = monitoring, AI, export, cleanup, other jobs
# =====================================================

app.conf.task_queues = (
    Queue("scraping"),
    Queue("enrichment"),
    Queue("default"),
)

app.conf.task_default_queue = "default"

app.conf.task_routes = {
    # Search / scraping
    "apps.searches.tasks.start_search_task": {"queue": "scraping"},
    "apps.searches.tasks.resume_search_task": {"queue": "scraping"},

    # Enrichment
    "apps.leads.tasks.enrich_lead_website_task": {"queue": "enrichment"},
    "apps.leads.tasks.enrich_search_leads_task": {"queue": "enrichment"},
    "apps.leads.tasks.bulk_enrich_leads_task": {"queue": "enrichment"},
    "apps.leads.tasks.finalize_enrichment_jobs_task": {"queue": "enrichment"},

    # Exports
    "apps.leads.tasks.generate_export_file_task": {"queue": "default"},

    # AI
    "apps.ai.tasks.*": {"queue": "default"},

    # Monitoring
    "apps.monitoring.tasks.*": {"queue": "default"},

    # Cleanup
    "apps.leads.tasks.cleanup_all_users_data_task": {"queue": "default"},
    "apps.leads.tasks.cleanup_user_data_task": {"queue": "default"},
}

app.autodiscover_tasks()