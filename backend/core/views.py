from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HotTopic
from .serializers import HotTopicSerializer
from .utils.crawler import fetch_douyin_hot, fetch_weibo_hot, fetch_zhihu_hot


class HotTopicListView(ListAPIView):
    serializer_class = HotTopicSerializer

    def get_queryset(self):
        return HotTopic.objects.order_by("-hot_value", "-created_at")


class CrawlHotTopicsView(APIView):
    def post(self, request: Request) -> Response:
        """触发一次实时热点抓取并入库。"""

        created_counts: dict[str, int] = {"Weibo": 0, "Douyin": 0, "Zhihu": 0}
        platforms: list[tuple[str, Any, Any]] = [
            ("Weibo", HotTopic.PlatformChoices.WEIBO, fetch_weibo_hot),
            ("Douyin", HotTopic.PlatformChoices.DOUYIN, fetch_douyin_hot),
            ("Zhihu", HotTopic.PlatformChoices.ZHIHU, fetch_zhihu_hot),
        ]

        for key, platform_choice, fetch_fn in platforms:
            items = fetch_fn()
            for item in items:
                _, created = HotTopic.objects.update_or_create(
                    title=item.title,
                    platform=platform_choice,
                    defaults={"hot_value": item.hot_value},
                )
                if created:
                    created_counts[key] += 1

        return Response(
            {"created": created_counts},
            status=status.HTTP_200_OK,
        )
