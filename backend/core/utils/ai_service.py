from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import OpenAI


logger = logging.getLogger(__name__)


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _client() -> OpenAI:
    api_key = _get_env("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def _mock_script(topic_title: str) -> list[dict[str, Any]]:
    """生成一份可用的 mock 分镜脚本。

    用于：
    - 开发环境未配置 LLM_API_KEY
    - 大模型调用失败 / 输出格式不符合预期
    """

    base = topic_title.strip() or "热点话题"
    lines = [
        f"大家好，今天我们聊聊：{base}。",
        "先用一句话概括核心看点，然后给你三个关键细节。",
        "接着从影响、原因、趋势三个角度快速拆解。",
        "最后总结一下：我们应该如何看待、如何应对。",
        "如果你想看更多类似热点解读，记得关注。",
    ]
    prompts = [
        "news anchor in studio, clean background, cinematic lighting",
        "timeline infographic, minimal style, high contrast",
        "people discussing, modern city street, documentary style",
        "data charts and icons, flat design, clear composition",
        "call to action end card, bold typography, vibrant colors",
    ]
    out: list[dict[str, Any]] = []
    for i, (txt, img) in enumerate(zip(lines, prompts), start=1):
        out.append(
            {
                "order": i,
                "text": txt,
                "image_prompt": img,
                "image_path": "",
                "audio_path": "",
                "duration": 4.0,
            }
        )
    return out


def generate_script(topic_title: str) -> list[dict[str, Any]]:
    """调用 DeepSeek 生成分镜脚本。

    返回 JSON 结构：
    [
      {
        "order": 1,
        "text": "...",
        "image_prompt": "...",
        "image_path": "",
        "audio_path": "",
        "duration": 5.0
      }
    ]

    注意：image_path/audio_path/duration 先返回占位，后续渲染任务再补齐。
    """

    topic_title = topic_title.strip()
    if not topic_title:
        raise ValueError("topic_title cannot be empty")

    if not os.getenv("LLM_API_KEY"):
        logger.warning("LLM_API_KEY not set; returning mock script")
        return _mock_script(topic_title)

    model = os.getenv("LLM_MODEL", "deepseek-chat")

    system_prompt = (
        "你是一个短视频分镜脚本生成器。"
        "请严格只输出 JSON 数组，不要输出任何解释文字。"
        "数组元素为分镜对象，字段必须包含："
        "order(整数，从1递增)、text(旁白台词，中文)、image_prompt(英文画面提示词)、"
        "image_path(字符串，先置空)、audio_path(字符串，先置空)、duration(数字，单位秒，先给合理估计)。"
        "总分镜数控制在 5 段左右。"
    )

    user_prompt = f"请为以下热点生成分镜脚本：{topic_title}"

    try:
        cli = _client()
        resp = cli.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        content = (resp.choices[0].message.content or "").strip()
        if not content:
            raise RuntimeError("LLM returned empty content")

        data: Any
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM output is not valid JSON: {e}") from e

        if not isinstance(data, list):
            raise RuntimeError("LLM output JSON must be a list")
    except Exception as e:
        logger.exception("LLM call failed; returning mock script: %s", e)
        return _mock_script(topic_title)

    normalized: list[dict[str, Any]] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "order": int(item.get("order") or i),
                "text": str(item.get("text") or "").strip(),
                "image_prompt": str(item.get("image_prompt") or "").strip(),
                "image_path": str(item.get("image_path") or ""),
                "audio_path": str(item.get("audio_path") or ""),
                "duration": float(item.get("duration") or 5.0),
            }
        )

    if not normalized:
        logger.warning("LLM output JSON list is empty or invalid; returning mock script")
        return _mock_script(topic_title)

    return normalized
