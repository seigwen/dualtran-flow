"""Pure translation helpers for the Flow Launcher plugin.

Kept free of Flow Launcher imports so the unit tests can exercise them without the host.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"


class TranslationError(RuntimeError):
    pass


def normalize_endpoint(endpoint: str) -> str:
    trimmed = (endpoint or "").strip().rstrip("/")
    if not trimmed.lower().startswith(("http://", "https://")):
        raise TranslationError(
            f'Endpoint must start with http:// or https:// (got "{endpoint}")'
        )
    return trimmed


def chat_completions_url(endpoint: str) -> str:
    base = normalize_endpoint(endpoint)
    if base.lower().endswith("/chat/completions"):
        return base
    if base.rsplit("/", 1)[-1].startswith("v") and base.rsplit("/", 1)[-1][1:].isdigit():
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def build_chat_payload(model: str, text: str, target: str) -> dict[str, Any]:
    return {
        "model": model,
        "temperature": 0,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You translate into {target}. Return only the translation, no commentary, "
                    "no quotes, and keep names and numbers exactly as they appear. "
                    f"If the text is already in {target}, return it unchanged."
                ),
            },
            {"role": "user", "content": text},
        ],
    }


def parse_chat_response(payload: Any) -> str:
    if isinstance(payload, dict) and payload.get("error"):
        message = payload["error"].get("message") if isinstance(payload["error"], dict) else payload["error"]
        raise TranslationError(str(message))
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise TranslationError("The provider returned an unexpected payload") from None
    if not isinstance(content, str) or not content.strip():
        raise TranslationError("The provider returned an empty translation")
    return content.strip()


def google_url(text: str, target: str, source: str = "auto") -> str:
    params = urllib.parse.urlencode(
        {"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text}
    )
    return f"{GOOGLE_ENDPOINT}?{params}"


def parse_google_response(payload: Any) -> str:
    try:
        rows = payload[0]
    except (IndexError, KeyError, TypeError):
        raise TranslationError("Unexpected response from Google Translate") from None
    if not isinstance(rows, list):
        raise TranslationError("Unexpected response from Google Translate")
    text = "".join(str(row[0]) for row in rows if isinstance(row, list) and row)
    text = text.strip()
    if not text:
        raise TranslationError("Google Translate returned an empty translation")
    return text


def _request(url: str, data: bytes | None, headers: dict[str, str]) -> Any:
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "ignore")[:200]
        raise TranslationError(f"HTTP {error.code}: {body}") from None
    except urllib.error.URLError as error:
        raise TranslationError(f"Network error: {error.reason}") from None
    except json.JSONDecodeError:
        raise TranslationError("The endpoint answered with something that is not JSON") from None


def translate(
    text: str,
    target: str,
    engine: str = "google",
    endpoint: str = "https://api.openai.com/v1",
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        raise TranslationError("Nothing to translate")
    if engine == "ai":
        url = chat_completions_url(endpoint)
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = build_chat_payload(model, cleaned, target)
        return parse_chat_response(_request(url, json.dumps(payload).encode("utf-8"), headers))
    return parse_google_response(_request(google_url(cleaned, target), None, {}))
