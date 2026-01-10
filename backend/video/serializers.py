from __future__ import annotations

from rest_framework import serializers

from .models import VideoProject, VideoScript


class VideoScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoScript
        fields = ("id", "project", "content", "created_at", "updated_at")


class VideoProjectSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    latest_script_id = serializers.SerializerMethodField()

    class Meta:
        model = VideoProject
        fields = (
            "id",
            "topic",
            "topic_title",
            "title",
            "latest_script_id",
            "status",
            "video_file",
            "video_url",
            "cover_image",
            "created_at",
            "updated_at",
        )

    def get_latest_script_id(self, obj: VideoProject) -> int | None:
        script = obj.scripts.order_by("-created_at").first()
        return script.id if script else None

    def get_video_url(self, obj: VideoProject) -> str | None:
        request = self.context.get("request")
        if not obj.video_file:
            return None
        try:
            url = obj.video_file.url
        except Exception:
            return None
        if request is None:
            return url
        return request.build_absolute_uri(url)
