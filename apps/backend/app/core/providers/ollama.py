from typing import Optional
from urllib.parse import urlparse

from app.core.providers.base import BaseProvider, ProviderDefaults


class OllamaProvider(BaseProvider):
    key = "ollama"
    aliases = ("ollama",)
    requires_api_key = False
    defaults = ProviderDefaults(
        base_url="http://127.0.0.1:11434/api",
        text_endpoint="/chat",
        image_endpoint="",
        video_endpoint="",
        video_fetch_endpoint="",
        audio_endpoint="",
    )

    def normalize_base_url(self, base_url: Optional[str]) -> str:
        normalized = super().normalize_base_url(base_url)
        parsed = urlparse(normalized)
        path = (parsed.path or "").rstrip("/")
        if not path:
            return f"{normalized}/api"
        return normalized
