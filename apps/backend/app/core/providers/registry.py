from typing import Dict, List, Optional

from app.core.providers.base import BaseProvider, ProviderDefaults
from app.core.providers.ollama import OllamaProvider
from app.core.providers.openai import OpenAIProvider
from app.core.providers.volcengine import VolcengineProvider

PLATFORM_OPENAI = "openai"
PLATFORM_OLLAMA = "ollama"
PLATFORM_VOLCENGINE = "volcengine"

_PROVIDERS: Dict[str, BaseProvider] = {
    PLATFORM_OPENAI: OpenAIProvider(),
    PLATFORM_OLLAMA: OllamaProvider(),
    PLATFORM_VOLCENGINE: VolcengineProvider(),
}

_ALIAS_TO_PLATFORM: Dict[str, str] = {}
for platform_key, provider in _PROVIDERS.items():
    aliases = set(provider.aliases or ())
    aliases.add(provider.key)
    aliases.add(platform_key)
    for alias in aliases:
        _ALIAS_TO_PLATFORM[str(alias).strip().lower()] = platform_key


def normalize_platform(platform: Optional[str]) -> str:
    value = (platform or PLATFORM_OPENAI).strip().lower()
    return _ALIAS_TO_PLATFORM.get(value, PLATFORM_OPENAI)


def get_provider(platform: Optional[str]) -> BaseProvider:
    return _PROVIDERS[normalize_platform(platform)]


def platform_defaults(platform: Optional[str]) -> ProviderDefaults:
    return get_provider(platform).defaults


def resolve_base_url(platform: Optional[str], base_url: Optional[str]) -> str:
    return get_provider(platform).normalize_base_url(base_url)


def resolve_endpoint(
    platform: Optional[str], endpoint_name: str, endpoint_value: Optional[str]
) -> str:
    return get_provider(platform).resolve_endpoint(endpoint_name, endpoint_value)


def requires_api_key(platform: Optional[str]) -> bool:
    return get_provider(platform).requires_api_key


def supported_platforms() -> List[str]:
    return list(_PROVIDERS.keys())
