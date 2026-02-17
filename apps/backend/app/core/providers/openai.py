from app.core.providers.base import BaseProvider, ProviderDefaults


class OpenAIProvider(BaseProvider):
    key = "openai"
    aliases = ("openai",)
    defaults = ProviderDefaults(
        base_url="https://api.openai.com/v1",
        text_endpoint="/chat/completions",
        image_endpoint="/images/generations",
        video_endpoint="/videos",
        video_fetch_endpoint="/videos/{task_id}",
        audio_endpoint="",
    )
