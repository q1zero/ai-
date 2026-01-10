from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import re
import requests


@dataclass(frozen=True, slots=True)
class WeiboHotItem:
    title: str
    hot_value: int
    rank: int
    fetched_at: datetime


def _mock_weibo_hot() -> list[WeiboHotItem]:
    now = datetime.now()
    return [
        WeiboHotItem(title=f"Mock 热搜 #{i}", hot_value=100000 - i * 137, rank=i, fetched_at=now)
        for i in range(1, 6)
    ]


def fetch_weibo_hot(timeout_seconds: int = 10) -> list[WeiboHotItem]:
    """抓取微博热搜。

    说明：微博真实接口/页面可能会频繁变动或触发反爬。
    因此这里先尝试一次轻量请求；若失败则返回 5 条 mock 数据，确保主流程可跑通。

    返回：热搜列表（包含 title/hot_value/rank/fetched_at）。
    """

    url = "https://weibo.com/ajax/statuses/hot_band"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://weibo.com/hot/search",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_seconds)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        band_list = data.get("data", {}).get("band_list")
        if not isinstance(band_list, list) or not band_list:
            return _mock_weibo_hot()

        now = datetime.now()
        items: list[WeiboHotItem] = []
        for idx, item in enumerate(band_list[:10], start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("word") or "").strip()
            if not title:
                continue
            raw_hot = item.get("raw_hot")
            hot_value = int(raw_hot) if isinstance(raw_hot, int) else 0
            items.append(
                WeiboHotItem(title=title, hot_value=hot_value, rank=idx, fetched_at=now)
            )

        return items or _mock_weibo_hot()
    except Exception:
        return _mock_weibo_hot()


def _mock_douyin_hot() -> list[WeiboHotItem]:
    """Mock Douyin hot topics."""
    now = datetime.now()
    return [
        WeiboHotItem(
            title=f"抖音热梗：{topic}",
            hot_value=2000000 - i * 150000,
            rank=i,
            fetched_at=now,
        )
        for i, topic in enumerate(
            ["科目三舞蹈", "哈尔滨旅游", "繁花电视剧", "龙年大吉", "AI视频生成"], start=1
        )
    ]


def fetch_douyin_hot(timeout_seconds: int = 10) -> list[WeiboHotItem]:
    """抓取抖音热搜（使用官方公开接口或 Mock）。"""
    # 抖音 web 热点接口通常需要复杂的 signature 验证。
    # 这里尝试一个公开的非官方接口，如果失败则 Mock。
    # 也可以直接返回 Mock，因为抖音反爬较严。
    try:
        url = "https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout_seconds)
        if resp.status_code == 200:
            data = resp.json()
            word_list = data.get("word_list", [])
            if word_list:
                now = datetime.now()
                items: list[WeiboHotItem] = []
                for idx, item in enumerate(word_list[:10], start=1):
                    title = item.get("word", "").strip()
                    hot_value = item.get("hot_value", 0)
                    if title:
                        items.append(
                            WeiboHotItem(
                                title=title,
                                hot_value=hot_value,
                                rank=idx,
                                fetched_at=now,
                            )
                        )
                return items
    except Exception:
        pass

    return _mock_douyin_hot()


def _mock_zhihu_hot() -> list[WeiboHotItem]:
    now = datetime.now()
    return [
        WeiboHotItem(
            title=f"知乎热榜：{topic}",
            hot_value=900000 - i * 65000,
            rank=i,
            fetched_at=now,
        )
        for i, topic in enumerate(
            ["AI 会取代哪些工作？", "今年就业形势如何？", "如何高效学习？", "新能源车能买吗？", "如何评价某热点事件？"],
            start=1,
        )
    ]


def fetch_zhihu_hot(timeout_seconds: int = 10) -> list[WeiboHotItem]:
    """抓取知乎热榜（失败则返回 mock）。"""

    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10&desktop=true"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.zhihu.com/hot",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_seconds)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        raw_items = data.get("data")
        if not isinstance(raw_items, list) or not raw_items:
            return _mock_zhihu_hot()

        now = datetime.now()
        items: list[WeiboHotItem] = []
        for idx, item in enumerate(raw_items[:10], start=1):
            if not isinstance(item, dict):
                continue
            target = item.get("target")
            if not isinstance(target, dict):
                continue
            title_area = target.get("title_area")
            if not isinstance(title_area, dict):
                continue
            title = str(title_area.get("text") or "").strip()
            if not title:
                continue
            detail_text = item.get("detail_text")
            hot_value = 0
            if isinstance(detail_text, str) and detail_text.strip():
                m = re.search(r"(\d+(?:\.\d+)?)", detail_text)
                if m:
                    num = float(m.group(1))
                    if "万" in detail_text:
                        num *= 10000
                    hot_value = int(num)
            elif isinstance(detail_text, (int, float)):
                hot_value = int(detail_text)
            items.append(
                WeiboHotItem(title=title, hot_value=hot_value, rank=idx, fetched_at=now)
            )

        return items or _mock_zhihu_hot()
    except Exception:
        return _mock_zhihu_hot()
