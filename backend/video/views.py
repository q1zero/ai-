from __future__ import annotations

from pathlib import Path
from typing import Any

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import HotTopic
from core.utils.ai_service import generate_script

from .engine import compose_video
from .models import VideoProject, VideoScript
from .serializers import VideoProjectSerializer, VideoScriptSerializer


class GenerateScriptView(APIView):
    def post(self, request: Request) -> Response:
        """创建项目并生成/保存脚本。

        支持：
        - 传入 title 自定义项目标题（用于视频库展示）。
        - 传入 content（脚本列表）时将直接保存，无需再次调用大模型。
        """

        topic_id = request.data.get("topic_id")
        if not topic_id:
            return Response({"detail": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = get_object_or_404(HotTopic, id=topic_id)

        title = request.data.get("title")
        project_title = str(title).strip() if title is not None else ""

        project = VideoProject.objects.create(
            topic=topic,
            title=project_title or topic.title,
            status=VideoProject.StatusChoices.DRAFT,
        )

        content = request.data.get("content")
        if content is not None:
            if not isinstance(content, list):
                return Response(
                    {"detail": "content must be a JSON list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not content:
                return Response(
                    {"detail": "content must be a non-empty JSON list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            script_data = content
        else:
            style = request.data.get("style")
            prompt = f"{topic.title}\n风格偏好：{style}" if style else topic.title
            script_data = generate_script(prompt)

        project.status = VideoProject.StatusChoices.WAIT_CONFIRM
        project.save(update_fields=["status", "updated_at"])

        script = VideoScript.objects.create(project=project, content=script_data)

        return Response(
            {
                "project_id": project.id,
                "script_id": script.id,
                "content": script.content,
            },
            status=status.HTTP_201_CREATED,
        )


class PreviewScriptView(APIView):
    def post(self, request: Request) -> Response:
        """生成脚本预览（不落库）。"""

        topic_id = request.data.get("topic_id")
        if not topic_id:
            return Response({"detail": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = get_object_or_404(HotTopic, id=topic_id)
        style = request.data.get("style")
        prompt = f"{topic.title}\n风格偏好：{style}" if style else topic.title
        script_data = generate_script(prompt)
        return Response({"content": script_data}, status=status.HTTP_200_OK)


class StartRenderView(APIView):
    def post(self, request: Request) -> Response:
        script_id = request.data.get("script_id")
        if not script_id:
            return Response({"detail": "script_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        script = get_object_or_404(VideoScript, id=script_id)

        content = request.data.get("content")
        if content is not None:
            if not isinstance(content, list):
                return Response(
                    {"detail": "content must be a JSON list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not content:
                return Response(
                    {"detail": "content must be a non-empty JSON list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            script.content = content
            script.save(update_fields=["content", "updated_at"])

        project = script.project
        project.status = VideoProject.StatusChoices.RENDERING
        project.save(update_fields=["status", "updated_at"])

        # 如果后续 Celery 配置完成，这里应改为触发异步任务（避免阻塞请求线程）。
        try:
            media_root = Path(getattr(settings, "MEDIA_ROOT", Path(settings.BASE_DIR) / "media"))
            out_dir = media_root / "videos"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"project_{project.id}.mp4"

            compose_video(script.content, str(out_path))

            rel_path = out_path.relative_to(media_root)
            project.video_file.name = str(rel_path).replace("\\", "/")
            project.status = VideoProject.StatusChoices.COMPLETED
            project.save(update_fields=["video_file", "status", "updated_at"])
        except Exception as e:
            project.status = VideoProject.StatusChoices.FAILED
            project.save(update_fields=["status", "updated_at"])
            return Response(
                {"detail": f"render failed: {type(e).__name__}: {e}", "project_id": project.id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"project_id": project.id, "status": project.status})


class VideoProjectView(APIView):
    def get(self, request: Request, project_id: int) -> Response:
        project = get_object_or_404(VideoProject, id=project_id)
        serializer = VideoProjectSerializer(project, context={"request": request})
        return Response(serializer.data)


class VideoProjectListView(APIView):
    def get(self, request: Request) -> Response:
        projects = VideoProject.objects.select_related("topic").order_by("-created_at")
        serializer = VideoProjectSerializer(projects, many=True, context={"request": request})
        return Response(serializer.data)


class VideoScriptView(APIView):
    def get(self, request: Request, script_id: int) -> Response:
        script = get_object_or_404(VideoScript, id=script_id)
        serializer = VideoScriptSerializer(script)
        return Response(serializer.data)
