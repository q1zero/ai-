from django.db import models

# Create your models here.


class VideoProject(models.Model):
    """视频项目。"""

    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", "DRAFT"
        WAIT_CONFIRM = "WAIT_CONFIRM", "WAIT_CONFIRM"
        RENDERING = "RENDERING", "RENDERING"
        COMPLETED = "COMPLETED", "COMPLETED"
        FAILED = "FAILED", "FAILED"

    topic: models.ForeignKey = models.ForeignKey(
        "core.HotTopic",
        on_delete=models.PROTECT,
        related_name="video_projects",
    )
    title: models.CharField = models.CharField(max_length=255, blank=True, default="")
    status: models.CharField = models.CharField(
        max_length=32,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    video_file: models.FileField = models.FileField(upload_to="videos/", blank=True, null=True)
    cover_image: models.ImageField = models.ImageField(
        upload_to="covers/", blank=True, null=True
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"VideoProject#{self.pk} ({self.status})"


class VideoScript(models.Model):
    """分镜脚本：以 JSON 存储分镜列表。"""

    project: models.ForeignKey = models.ForeignKey(
        VideoProject,
        on_delete=models.CASCADE,
        related_name="scripts",
    )
    content: models.JSONField = models.JSONField(default=list)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"VideoScript#{self.pk} for project#{self.project_id}"
