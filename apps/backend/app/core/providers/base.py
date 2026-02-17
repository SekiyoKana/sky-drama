from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ProviderDefaults:
    base_url: str
    text_endpoint: str
    image_endpoint: str
    video_endpoint: str
    video_fetch_endpoint: str
    audio_endpoint: str


class BaseProvider:
    key: str = ""
    aliases: Tuple[str, ...] = ()
    defaults: ProviderDefaults = ProviderDefaults(
        base_url="",
        text_endpoint="",
        image_endpoint="",
        video_endpoint="",
        video_fetch_endpoint="",
        audio_endpoint="",
    )
    requires_api_key: bool = True

    def normalize_base_url(self, base_url: Optional[str]) -> str:
        candidate = (base_url or "").strip()
        if candidate:
            return candidate.rstrip("/")
        return self.defaults.base_url

    def resolve_endpoint(self, endpoint_name: str, endpoint_value: Optional[str]) -> str:
        if not hasattr(self.defaults, endpoint_name):
            raise ValueError(f"Unknown endpoint field: {endpoint_name}")

        default_value = getattr(self.defaults, endpoint_name)
        candidate = (endpoint_value or "").strip()
        if not candidate:
            return default_value
        if not candidate.startswith("/"):
            return f"/{candidate}"
        return candidate
