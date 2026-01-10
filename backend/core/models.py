from django.db import models

# Create your models here.


class HotTopic(models.Model):
    """热点话题。"""

    class PlatformChoices(models.TextChoices):
        WEIBO = "Weibo", "Weibo"
        ZHIHU = "Zhihu", "Zhihu"
        BAIDU = "Baidu", "Baidu"
        DOUYIN = "Douyin", "Douyin"

    title: models.CharField = models.CharField(max_length=255)
    platform: models.CharField = models.CharField(
        max_length=32,
        choices=PlatformChoices.choices,
    )
    hot_value: models.IntegerField = models.IntegerField(default=0)
    summary: models.TextField = models.TextField(blank=True, default="")
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    is_used: models.BooleanField = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "platform"],
                name="uniq_hot_topic_title_platform",
            )
        ]

    def __str__(self) -> str:
        return f"[{self.platform}] {self.title}"
