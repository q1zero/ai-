from __future__ import annotations

from django.urls import path

from .views import CrawlHotTopicsView, HotTopicListView

urlpatterns = [
    path("hot-topics/", HotTopicListView.as_view(), name="hot-topic-list"),
    path("crawl-hot-topics/", CrawlHotTopicsView.as_view(), name="crawl-hot-topics"),
]
