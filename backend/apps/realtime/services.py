from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings


def realtime_enabled():
    return bool(getattr(settings, "REALTIME_ENABLED", True))


def get_user_group_name(user_id):
    return f"user_{user_id}"


def send_realtime_event(user_id, payload):
    """
    Send real-time event to one user.
    Safe to call from normal Django views or Celery tasks.
    """

    if not realtime_enabled():
        return False

    if not user_id or not payload:
        return False

    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            return False

        async_to_sync(channel_layer.group_send)(
            get_user_group_name(user_id),
            {
                "type": "realtime.event",
                "payload": payload,
            },
        )

        return True

    except Exception:
        return False