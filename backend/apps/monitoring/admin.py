from django.contrib import admin

from .models import SystemEvent


@admin.register(SystemEvent)
class SystemEventAdmin(admin.ModelAdmin):
    list_display = [
        "level",
        "source",
        "title",
        "user",
        "task_name",
        "object_type",
        "object_id",
        "resolved",
        "created_at",
    ]

    list_filter = [
        "level",
        "source",
        "resolved",
        "created_at",
    ]

    search_fields = [
        "title",
        "message",
        "task_name",
        "task_id",
        "object_type",
        "object_id",
        "user__email",
    ]

    readonly_fields = [
        "created_at",
    ]

    actions = [
        "mark_resolved",
        "mark_unresolved",
    ]

    def mark_resolved(self, request, queryset):
        from django.utils import timezone

        queryset.update(resolved=True, resolved_at=timezone.now())

    def mark_unresolved(self, request, queryset):
        queryset.update(resolved=False, resolved_at=None)