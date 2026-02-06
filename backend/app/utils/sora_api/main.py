from typing import Optional

from app.utils.sora_api import Base, Yi, Kie

class SoraApiFormatter:
    _formatters = [Yi, Kie]

    @classmethod
    def search(cls, base_url: str) -> Optional[Base]:
        if not base_url:
            return None
        base_url_lower = base_url.lower()
        for fmt_cls in cls._formatters:
            fmt = fmt_cls()
            if fmt.match(base_url_lower):
                return fmt
        return None
