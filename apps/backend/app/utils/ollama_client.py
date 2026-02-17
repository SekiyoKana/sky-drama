import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from app.utils.http_client import request as http_request


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _build_headers(api_key: Optional[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
    }
    token = (api_key or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _raise_ollama_error(response) -> None:
    detail = response.text
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("error"):
            detail = str(payload["error"])
    except Exception:
        pass
    raise RuntimeError(f"Ollama request failed ({response.status_code}): {detail}")


class _OllamaResponseStream:
    def __init__(self, response):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def close(self):
        try:
            self._response.close()
        except Exception:
            pass

    def __iter__(self):
        for raw_line in self._response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            if payload.get("error"):
                raise RuntimeError(str(payload["error"]))

            message = payload.get("message") if isinstance(payload, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if content:
                yield SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content=content),
                        )
                    ]
                )

            if payload.get("done"):
                break


class _OllamaCompletions:
    def __init__(self, parent: "OllamaClient"):
        self._parent = parent

    def create(self, *, model: str, messages: List[Dict[str, Any]], stream: bool = True, **kwargs):
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if kwargs:
            payload.update(kwargs)

        response = http_request(
            "POST",
            self._parent.chat_url,
            json=payload,
            headers=self._parent.headers,
            stream=True,
            timeout=(10.0, 600.0),
        )
        if response.status_code != 200:
            _raise_ollama_error(response)
        return _OllamaResponseStream(response)


class _OllamaChat:
    def __init__(self, parent: "OllamaClient"):
        self.completions = _OllamaCompletions(parent)


class OllamaClient:
    def __init__(self, base_url: str, api_key: Optional[str], chat_endpoint: str = "/chat"):
        self.base_url = base_url.rstrip("/")
        endpoint = chat_endpoint if chat_endpoint.startswith("/") else f"/{chat_endpoint}"
        self.chat_url = _join_url(self.base_url, endpoint)
        self.headers = _build_headers(api_key)
        self.chat = _OllamaChat(self)


def list_ollama_models(base_url: str, api_key: Optional[str]) -> List[str]:
    tags_url = _join_url(base_url, "/tags")
    response = http_request(
        "GET",
        tags_url,
        headers=_build_headers(api_key),
        timeout=(10.0, 30.0),
    )
    if response.status_code != 200:
        _raise_ollama_error(response)

    payload = response.json() if response.content else {}
    models = payload.get("models") if isinstance(payload, dict) else []
    if not isinstance(models, list):
        return []

    names = []
    for item in models:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return sorted(set(names))
