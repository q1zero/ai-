from __future__ import annotations

from rest_framework import serializers

from .models import HotTopic


class HotTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotTopic
        fields = (
            "id",
            "title",
            "platform",
            "hot_value",
            "summary",
            "created_at",
            "is_used",
        )
