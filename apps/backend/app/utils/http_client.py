import logging
import os
import time
from typing import Any, Dict, Optional, Tuple, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Default timeouts: (connect, read)
DEFAULT_TIMEOUT: Tuple[float, float] = (10.0, 600.0)

_session: Optional[requests.Session] = None


def _ensure_no_proxy_defaults() -> None:
    """
    Ensure localhost bypasses proxy to avoid self-call failures in Docker/Tauri.
    """
    defaults = ["127.0.0.1", "localhost"]
    for key in ("NO_PROXY", "no_proxy"):
        current = os.environ.get(key, "")
        parts = [p.strip() for p in current.split(",") if p.strip()]
        changed = False
        for item in defaults:
            if item not in parts:
                parts.append(item)
                changed = True
        if changed or (not current and parts):
            os.environ[key] = ",".join(parts)


def _apply_proxy_env_aliases() -> None:
    """
    Support custom proxy envs without overwriting standard ones.
    Users can set SKYDRAMA_HTTP_PROXY / SKYDRAMA_HTTPS_PROXY.
    """
    for std_key, alias_key in (
        ("HTTP_PROXY", "SKYDRAMA_HTTP_PROXY"),
        ("HTTPS_PROXY", "SKYDRAMA_HTTPS_PROXY"),
    ):
        if not os.environ.get(std_key) and os.environ.get(alias_key):
            os.environ[std_key] = os.environ[alias_key]


def _build_session() -> requests.Session:
    init_network_env()

    session = requests.Session()
    # Keep default trust_env=True to honor proxy envs when present.
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=None,  # allow retries for all methods (POST included)
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # A concise UA helps with some proxy/WAF setups.
    session.headers.update({"User-Agent": "Sky-Drama/0.1"})
    return session


def init_network_env() -> None:
    """
    Initialize proxy-related environment defaults.
    Safe to call multiple times.
    """
    _apply_proxy_env_aliases()
    _ensure_no_proxy_defaults()


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = _build_session()
    return _session


def request(
    method: str,
    url: str,
    *,
    timeout: Optional[Union[Tuple[float, float], float]] = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Wrapper around requests with retry + sane defaults.
    """
    session = get_session()
    final_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT

    try:
        return session.request(method, url, timeout=final_timeout, **kwargs)
    except requests.exceptions.RequestException as e:
        # Add context for easier debugging
        logger.error(f"[HTTP] {method} {url} failed: {e}")
        raise


def download_headers() -> Dict[str, str]:
    """
    Use curl-like UA for OSS/CDN image downloads to avoid referer/UA blocks.
    """
    return {
        "User-Agent": "curl/7.79.1",
        "Accept": "*/*",
    }
