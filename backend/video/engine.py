from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any
from urllib.parse import quote

import edge_tts
import requests
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
try:
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
except ModuleNotFoundError:  # MoviePy v2+ doesn't expose moviepy.editor
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips


async def generate_audio(text: str, filename: str) -> str:
    """使用 Edge-TTS 生成中文语音 MP3。"""

    text = text.strip()
    if not text:
        raise ValueError("text cannot be empty")

    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    communicate = edge_tts.Communicate(text=text, voice="zh-CN-YunxiNeural")
    await communicate.save(str(out_path))
    return str(out_path)


def download_image(prompt: str, filename: str, *, width: int = 1280, height: int = 720) -> str:
    """使用 SiliconFlow 文生图 API 生成图片。

    - 端点: https://api.siliconflow.cn/v1/images/generations
    - 模型: black-forest-labs/FLUX.1-schnell
    - 失败兜底: https://picsum.photos/1280/720
    """

    prompt = prompt.strip() or "A cinematic photo"
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_siliconflow_key() -> str | None:
        try:
            from django.conf import settings

            key = getattr(settings, "LLM_API_KEY", None) or getattr(
                settings, "SILICONFLOW_API_KEY", None
            )
            if isinstance(key, str) and key.strip():
                return key.strip()
        except Exception:
            pass

        key = os.getenv("LLM_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
        return key.strip() if isinstance(key, str) and key.strip() else None

    def _placeholder(note: str) -> None:
        img = Image.new("RGB", (width, height), color=(245, 246, 250))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        title = "IMAGE PLACEHOLDER"
        draw.rectangle([(0, 0), (width, 120)], fill=(30, 30, 30))
        draw.text((40, 35), title, fill=(255, 255, 255), font=font)

        body = f"Prompt: {prompt}"[:500]
        draw.text((40, 160), body, fill=(30, 30, 30), font=font)
        draw.text((40, height - 80), note[:200], fill=(120, 120, 120), font=font)
        img.save(out_path, format="JPEG", quality=92)

    session = requests.Session()
    session.trust_env = False

    api_key = _get_siliconflow_key()
    if not api_key:
        print("[download_image] Missing API key (LLM_API_KEY/SILICONFLOW_API_KEY), fallback to picsum")
    else:
        try:
            resp = session.post(
                "https://api.siliconflow.cn/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": prompt,
                    "image_size": "1024x576",
                },
                timeout=90,
            )
            resp.raise_for_status()
            payload: Any = resp.json()
            image_url = payload["data"][0]["url"]

            img_resp = session.get(image_url, timeout=90)
            img_resp.raise_for_status()
            out_path.write_bytes(img_resp.content)
            return str(out_path)
        except Exception as e:
            print(f"[download_image] SiliconFlow generation failed, fallback to picsum: {e}")

    try:
        img_resp = session.get("https://picsum.photos/1280/720", timeout=60)
        img_resp.raise_for_status()
        out_path.write_bytes(img_resp.content)
        return str(out_path)
    except Exception as e:
        print(f"[download_image] Picsum fallback failed, use placeholder: {e}")
        _placeholder("(SiliconFlow + picsum failed; generated locally)")
        return str(out_path)


def _resolve_temp_root() -> Path:
    """优先使用 Django 的 media/temp；否则回退到系统临时目录。"""

    try:
        from django.conf import settings

        base_dir = Path(getattr(settings, "BASE_DIR"))
        media_root = Path(getattr(settings, "MEDIA_ROOT", base_dir / "media"))
        temp_root = media_root / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        return temp_root
    except Exception:
        root = Path(tempfile.gettempdir()) / "autovideo_gen"
        root.mkdir(parents=True, exist_ok=True)
        return root


def _ensure_parent_dir(path: str | os.PathLike[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _run_async(coro: Any) -> Any:
    """在同步函数中执行异步协程。

    - 若当前线程没有正在运行的事件循环：直接 asyncio.run
    - 若当前线程已有事件循环在跑：在新线程里 asyncio.run，避免 RuntimeError
    """

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, Any] = {}

    def runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _with_duration(clip: Any, duration: float) -> Any:
    if hasattr(clip, "set_duration"):
        return clip.set_duration(duration)
    return clip.with_duration(duration)


def _with_audio(clip: Any, audio: Any) -> Any:
    if hasattr(clip, "set_audio"):
        return clip.set_audio(audio)
    return clip.with_audio(audio)


def _zoom_in(clip: Any, *, duration: float, zoom_factor: float = 0.08) -> Any:
    resize_fn = getattr(clip, "resize", None) or getattr(clip, "resized", None)
    if resize_fn is None:
        return clip

    return resize_fn(lambda t: 1.0 + zoom_factor * (t / max(duration, 0.001)))


def compose_video(script_data: list[dict[str, Any]], output_path: str) -> str:
    """根据脚本数据下载素材并合成视频。

    script_data 形如：
    [{"order": 1, "text": "...", "image_prompt": "...", ...}]

    output_path: 生成的 mp4 路径。
    """

    if not isinstance(script_data, list) or not script_data:
        raise ValueError("script_data must be a non-empty list")

    _ensure_parent_dir(output_path)

    temp_root = _resolve_temp_root()
    work_dir = Path(tempfile.mkdtemp(prefix="compose_", dir=str(temp_root)))

    clips: list[ImageClip] = []
    audio_clips: list[AudioFileClip] = []

    try:
        for idx, seg in enumerate(script_data, start=1):
            if not isinstance(seg, dict):
                continue

            text = str(seg.get("text") or "").strip()
            image_prompt = str(seg.get("image_prompt") or "").strip() or "A cinematic photo"

            image_path = work_dir / f"{idx:02d}_img.jpg"
            audio_path = work_dir / f"{idx:02d}_audio.mp3"

            download_image(image_prompt, str(image_path))
            _run_async(generate_audio(text or "（此分镜无旁白）", str(audio_path)))

            audio_clip = AudioFileClip(str(audio_path))
            duration = max(float(audio_clip.duration or 0), 0.1)

            clip = ImageClip(str(image_path))
            clip = _with_duration(clip, duration)

            # Zoom-in：从 1.00 放大到 1.08（线性），并保持居中
            clip = _zoom_in(clip, duration=duration, zoom_factor=0.08)

            clip = _with_audio(clip, audio_clip)

            clips.append(clip)
            audio_clips.append(audio_clip)

        if not clips:
            raise RuntimeError("No valid segments found in script_data")

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(work_dir / "temp-audio.m4a"),
            remove_temp=True,
            threads=2,
        )
        return output_path
    finally:
        for c in clips:
            try:
                c.close()
            except Exception:
                pass
        for a in audio_clips:
            try:
                a.close()
            except Exception:
                pass

        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
