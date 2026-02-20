import json
from typing import Any, Dict, List

from ..utils.llm import stream_llm_response

name = "novel-chapter-writer"
description = "根据雪花规划、选定角色与场景，生成章节正文。"

input_schema = {
    "type": "object",
    "properties": {
        "chapter_brief": {"type": "string"},
        "one_sentence": {"type": "string"},
        "chapter_summary": {"type": "string"},
        "major_beats": {"type": "array"},
        "selected_characters": {"type": "array"},
        "selected_scenes": {"type": "array"},
        "target_words": {"type": "integer"},
    },
    "required": ["chapter_brief"],
}


def _compact_characters(items: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not isinstance(items, list):
        return rows
    for item in items:
        if not isinstance(item, dict):
            continue
        row = {
            "id": str(item.get("id") or "").strip(),
            "name": str(item.get("name") or item.get("title") or "").strip(),
            "role": str(item.get("role") or item.get("subtitle") or "").strip(),
            "description": str(item.get("description") or "").strip(),
        }
        if row["name"]:
            rows.append(row)
    return rows[:20]


def _compact_scenes(items: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not isinstance(items, list):
        return rows
    for item in items:
        if not isinstance(item, dict):
            continue
        row = {
            "id": str(item.get("id") or "").strip(),
            "name": str(item.get("location_name") or item.get("name") or item.get("title") or "").strip(),
            "mood": str(item.get("mood") or item.get("subtitle") or "").strip(),
            "description": str(item.get("description") or "").strip(),
        }
        if row["name"]:
            rows.append(row)
    return rows[:20]


def _coerce_major_beats(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    out: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out[:12]


def main(
    prompt: str = "",
    chapter_brief: str = "",
    one_sentence: str = "",
    chapter_summary: str = "",
    major_beats: Any = None,
    selected_characters: Any = None,
    selected_scenes: Any = None,
    perspective: str = "third",
    tone: str = "cinematic",
    length: str = "medium",
    target_words: int = 1000,
    language: str = "zh-CN",
    client=None,
    model_name: str = "gpt-4o",
    **kwargs,
):
    safe_target_words = max(200, min(int(target_words or 1000), 12000))

    context_payload = {
        "chapter_brief": str(chapter_brief or prompt or "").strip(),
        "one_sentence": str(one_sentence or "").strip(),
        "chapter_summary": str(chapter_summary or "").strip(),
        "major_beats": _coerce_major_beats(major_beats),
        "selected_characters": _compact_characters(selected_characters),
        "selected_scenes": _compact_scenes(selected_scenes),
        "writing_config": {
            "perspective": str(perspective or "third"),
            "tone": str(tone or "cinematic"),
            "length": str(length or "medium"),
            "target_words": safe_target_words,
            "language": str(language or "zh-CN"),
        },
    }

    system_prompt = """
你是专业小说作者。请按照用户给出的雪花写作规划写出“章节正文”。

约束：
- 输出只包含最终章节正文，不要解释，不要标题，不要 markdown。
- 必须优先使用给定角色与场景，不要凭空新增核心角色。
- 按 major_beats 顺序推进剧情。
- 保持叙事连贯，有画面感，避免清单式写法。
- 字数尽量接近 target_words（允许上下 15% 浮动）。
"""

    user_prompt = (
        "请根据以下章节上下文生成正文：\n"
        + json.dumps(context_payload, ensure_ascii=False, indent=2)
    )

    return stream_llm_response(client, model_name, system_prompt, user_prompt)
