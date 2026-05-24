from rest_framework import serializers

from .models import SystemEvent


class SystemEventSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = SystemEvent
        fields = [
            "id",
            "user",
            "user_email",
            "level",
            "source",
            "title",
            "message",
            "task_name",
            "task_id",
            "object_type",
            "object_id",
            "metadata",
            "resolved",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_email(self, obj):
        if obj.user:
            return getattr(obj.user, "email", None)

        return None