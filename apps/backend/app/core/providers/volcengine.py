from typing import Optional

from app.core.providers.base import BaseProvider, ProviderDefaults


class VolcengineProvider(BaseProvider):
    key = "volcengine"
    aliases = (
        "volcengine",
        "ark",
        "doubao",
        "volcano",
        "volc",
        "huoshan",
        "火山引擎",
    )
    defaults = ProviderDefaults(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        text_endpoint="/chat/completions",
        image_endpoint="/images/generations",
        video_endpoint="/contents/generations/tasks",
        video_fetch_endpoint="/contents/generations/tasks/{task_id}",
        audio_endpoint="",
    )

    def resolve_endpoint(self, endpoint_name: str, endpoint_value: Optional[str]) -> str:
        candidate = (endpoint_value or "").strip()

        if endpoint_name == "video_endpoint" and candidate in {"", "videos", "/videos"}:
            candidate = ""

        if endpoint_name == "video_fetch_endpoint" and candidate in {
            "",
            "videos/{task_id}",
            "/videos/{task_id}",
            "contents/generations/tasks",
            "/contents/generations/tasks",
        }:
            candidate = ""

        return super().resolve_endpoint(endpoint_name, candidate)
