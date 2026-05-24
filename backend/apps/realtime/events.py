from .services import send_realtime_event


def send_search_started(user_id, search):
    return send_realtime_event(
        user_id,
        {
            "type": "search_started",
            "search_id": search.id,
            "status": search.status,
            "progress": search.progress(),
            "message": "Search started.",
        },
    )


def send_search_progress(user_id, search, query_task=None):
    payload = {
        "type": "search_progress",
        "search_id": search.id,
        "status": search.status,
        "progress": search.progress(),
        "completed_tasks": search.completed_tasks,
        "failed_tasks": search.failed_tasks,
        "total_tasks": search.total_tasks,
    }

    if query_task:
        payload["query_task"] = {
            "id": query_task.id,
            "keyword": query_task.keyword,
            "location": query_task.location,
            "status": query_task.status,
            "leads_found": query_task.leads_found,
            "processed_index": query_task.processed_index,
        }

    return send_realtime_event(user_id, payload)


def send_search_completed(user_id, search):
    return send_realtime_event(
        user_id,
        {
            "type": "search_completed",
            "search_id": search.id,
            "status": search.status,
            "progress": search.progress(),
            "message": "Search completed.",
        },
    )


def send_search_failed(user_id, search, error_message=None):
    return send_realtime_event(
        user_id,
        {
            "type": "search_failed",
            "search_id": search.id,
            "status": search.status,
            "error_message": error_message or search.error_message,
        },
    )


def send_lead_found(user_id, lead):
    return send_realtime_event(
        user_id,
        {
            "type": "lead_found",
            "lead": {
                "id": lead.id,
                "search_id": lead.search_id,
                "name": lead.name,
                "phone": lead.phone,
                "website": lead.website,
                "email_1": lead.email_1,
                "rating": lead.rating,
                "review_count": lead.review_count,
                "address": lead.address,
                "website_status": lead.website_status,
                "status": lead.status,
                "lead_score": lead.lead_score,
                "opportunity_score": lead.opportunity_score,
                "created_at": lead.created_at,
            },
        },
    )


def send_enrichment_started(user_id, job):
    return send_realtime_event(
        user_id,
        {
            "type": "enrichment_started",
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "total_items": job.total_items,
        },
    )


def send_enrichment_progress(user_id, job):
    done = job.completed_items + job.failed_items + job.skipped_items
    progress = 0

    if job.total_items:
        progress = min(int((done / job.total_items) * 100), 100)

    return send_realtime_event(
        user_id,
        {
            "type": "enrichment_progress",
            "job_id": job.id,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "skipped_items": job.skipped_items,
            "progress": progress,
        },
    )


def send_lead_enriched(user_id, lead):
    return send_realtime_event(
        user_id,
        {
            "type": "lead_enriched",
            "lead_id": lead.id,
            "search_id": lead.search_id,
            "website_status": lead.website_status,
            "website_platform": lead.website_platform,
            "email_1": lead.email_1,
            "email_confidence": lead.email_confidence,
            "enrichment_status": lead.enrichment_status,
            "lead_score": lead.lead_score,
            "opportunity_score": lead.opportunity_score,
        },
    )


def send_export_started(user_id, export_history):
    return send_realtime_event(
        user_id,
        {
            "type": "export_started",
            "export_id": export_history.id,
            "status": export_history.status,
            "export_type": export_history.export_type,
            "export_scope": export_history.export_scope,
            "total_rows": export_history.total_rows,
        },
    )


def send_export_completed(user_id, export_history):
    return send_realtime_event(
        user_id,
        {
            "type": "export_completed",
            "export_id": export_history.id,
            "status": export_history.status,
            "file_name": export_history.file_name,
            "total_rows": export_history.total_rows,
            "download_url": f"/api/leads/exports/{export_history.id}/download/",
        },
    )


def send_export_failed(user_id, export_history):
    return send_realtime_event(
        user_id,
        {
            "type": "export_failed",
            "export_id": export_history.id,
            "status": export_history.status,
            "error_message": export_history.error_message,
        },
    )


def send_notification(user_id, title, message, level="info"):
    return send_realtime_event(
        user_id,
        {
            "type": "notification",
            "title": title,
            "message": message,
            "level": level,
        },
    )
    
def send_ai_job_started(user_id, job):
    return send_realtime_event(
        user_id,
        {
            "type": "ai_job_started",
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "total_items": job.total_items,
        },
    )


def send_ai_job_progress(user_id, job):
    done = job.completed_items + job.failed_items + job.skipped_items
    progress = 0

    if job.total_items:
        progress = min(int((done / job.total_items) * 100), 100)

    return send_realtime_event(
        user_id,
        {
            "type": "ai_job_progress",
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "skipped_items": job.skipped_items,
            "progress": progress,
        },
    )


def send_ai_lead_completed(user_id, job, lead, insight):
    return send_realtime_event(
        user_id,
        {
            "type": "ai_lead_completed",
            "job_id": job.id if job else None,
            "lead_id": lead.id,
            "ai_priority": insight.ai_priority,
            "ai_summary": insight.ai_summary,
            "ai_suggested_offer": insight.ai_suggested_offer,
            "ai_best_channel": insight.ai_best_channel,
        },
    )


def send_ai_job_completed(user_id, job):
    return send_realtime_event(
        user_id,
        {
            "type": "ai_job_completed",
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "skipped_items": job.skipped_items,
            "progress": job.progress(),
        },
    )


def send_ai_job_failed(user_id, job):
    return send_realtime_event(
        user_id,
        {
            "type": "ai_job_failed",
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "error_message": job.error_message,
        },
    )