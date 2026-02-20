import json
from typing import Any

from ..utils.llm import stream_llm_response

name = "novel-expansion-assistant"
description = "针对用户选中文本进行扩写或改写。"

input_schema = {
    "type": "object",
    "properties": {
        "selected_text": {"type": "string"},
        "instruction": {"type": "string"},
        "mode": {"type": "string", "enum": ["expand", "rewrite"]},
    },
    "required": ["selected_text"],
}


def _safe_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit]


def main(
    prompt: str = "",
    selected_text: str = "",
    instruction: str = "",
    mode: str = "expand",
    before_context: str = "",
    after_context: str = "",
    language: str = "zh-CN",
    target_words: int = 0,
    client=None,
    model_name: str = "gpt-4o",
    **kwargs,
):
    selected = _safe_text(selected_text or prompt, 4000)
    if not selected:
        selected = ""

    op_mode = str(mode or "expand").strip().lower()
    if op_mode not in {"expand", "rewrite"}:
        op_mode = "expand"

    safe_target = 0
    try:
        safe_target = max(0, min(int(target_words or 0), 6000))
    except Exception:
        safe_target = 0

    context_payload = {
        "mode": op_mode,
        "language": str(language or "zh-CN"),
        "instruction": _safe_text(instruction, 800),
        "selected_text": selected,
        "before_context": _safe_text(before_context, 1200),
        "after_context": _safe_text(after_context, 1200),
        "target_words": safe_target,
    }

    system_prompt = """
你是小说编辑助手。请只输出“替换文本本体”。

规则：
- mode=expand: 在保留原意的基础上扩写细节、动作、情绪和环境。
- mode=rewrite: 按用户要求重写，可调整表达和节奏，但要与上下文一致。
- 若给出了 target_words（>0），尽量接近该字数。
- 不要输出解释、标注、引号、前后缀说明，也不要输出 markdown。
"""

    user_prompt = (
        "请处理以下文本片段并返回替换后的正文：\n"
        + json.dumps(context_payload, ensure_ascii=False, indent=2)
    )

    return stream_llm_response(client, model_name, system_prompt, user_prompt)
