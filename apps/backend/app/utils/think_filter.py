import re
from typing import Any

_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>[\s\S]*?</think>", re.IGNORECASE)
_THINK_OPEN_RE = re.compile(r"<think\b[^>]*>[\s\S]*$", re.IGNORECASE)
_THINK_TAG_RE = re.compile(r"</?think\b[^>]*>", re.IGNORECASE)


def strip_think_segments(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text

    cleaned = _THINK_BLOCK_RE.sub("", text)
    cleaned = _THINK_OPEN_RE.sub("", cleaned)
    cleaned = _THINK_TAG_RE.sub("", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_think_payload(value: Any) -> Any:
    if isinstance(value, str):
        return strip_think_segments(value)
    if isinstance(value, list):
        return [sanitize_think_payload(item) for item in value]
    if isinstance(value, dict):
        return {k: sanitize_think_payload(v) for k, v in value.items()}
    return value
