import json
from typing import Any, Dict, List

from ..utils.llm import stream_llm_response

name = "novel-snowflake-planner"
description = "基于雪花写作法，先将章节简介规划为可确认的章节蓝图。"

input_schema = {
    "type": "object",
    "properties": {
        "chapter_brief": {
            "type": "string",
            "description": "章节简介或章节目标",
        },
        "characters": {
            "type": "array",
            "description": "可选角色列表",
        },
        "scenes": {
            "type": "array",
            "description": "可选场景列表",
        },
    },
    "required": ["chapter_brief"],
}


def _compact_character_rows(items: Any) -> List[Dict[str, str]]:
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
        if row["id"] and row["name"]:
            rows.append(row)
    return rows[:40]


def _compact_scene_rows(items: Any) -> List[Dict[str, str]]:
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
        if row["id"] and row["name"]:
            rows.append(row)
    return rows[:40]


def main(
    prompt: str = "",
    chapter_brief: str = "",
    title: str = "",
    description: str = "",
    characters: Any = None,
    scenes: Any = None,
    existing_draft: str = "",
    language: str = "zh-CN",
    client=None,
    model_name: str = "gpt-4o",
    **kwargs,
):
    brief = str(chapter_brief or description or prompt or "").strip()

    compact_characters = _compact_character_rows(characters)
    compact_scenes = _compact_scene_rows(scenes)

    context_payload = {
        "chapter_title": str(title or "").strip(),
        "chapter_brief": brief,
        "language": str(language or "zh-CN"),
        "existing_draft": str(existing_draft or "")[:1200],
        "candidate_characters": compact_characters,
        "candidate_scenes": compact_scenes,
    }

    system_prompt = """
你是小说策划编辑。你必须使用“雪花写作法”的前两步：
1) 先产出一句话核心梗概（one_sentence）。
2) 再扩展成一段章节摘要（chapter_summary）。
3) 给出 4-8 条章节关键节拍（major_beats）。
4) 基于用户提供的候选池，建议本章出场角色与场景。

输出必须是一个 JSON 对象，且只能输出 JSON，不要 Markdown、不要解释、不要注释。

JSON schema:
{
  "one_sentence": "string",
  "chapter_summary": "string",
  "major_beats": ["string"],
  "character_suggestions": [
    {"id": "string", "name": "string", "reason": "string"}
  ],
  "scene_suggestions": [
    {"id": "string", "name": "string", "reason": "string"}
  ]
}

硬性约束：
- character_suggestions 与 scene_suggestions 的 id 必须来自输入候选池，不能虚构新 id。
- 如果候选池不足，可以返回空数组。
- 语言与章节简介保持一致（通常是中文）。
"""

    user_prompt = (
        "请根据以下上下文给出章节规划 JSON：\n"
        + json.dumps(context_payload, ensure_ascii=False, indent=2)
    )

    return stream_llm_response(client, model_name, system_prompt, user_prompt)
