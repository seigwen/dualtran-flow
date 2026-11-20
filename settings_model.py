"""Single source of truth for Flow's settings, catalogue and legacy migration.

The Tk settings window, the JSON-RPC query path and the conformance payload generator all
import this module, so the rendered controls and the gate cannot describe different products.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG_FILE = HERE / "catalog.json"
BUILTIN_FILE = HERE / "builtin-providers.json"
SETTINGS_FILE = HERE / "settings.json"
CUSTOM_ID = "_custom_flow"
PLACEHOLDER_VALUES = {
    "",
    "Select a provider",
    "请选择 AI 提供商",
    "请选择提供商",
    "Select a model",
    "请选择模型",
}

LANGUAGES = [
    ("en", "English (en)"),
    ("zh-CN", "Chinese (Simplified) (zh-CN)"),
    ("zh-TW", "Chinese (Traditional) (zh-TW)"),
    ("ja", "Japanese (ja)"),
    ("ko", "Korean (ko)"),
    ("es", "Spanish (es)"),
    ("fr", "French (fr)"),
    ("de", "German (de)"),
    ("it", "Italian (it)"),
    ("pt", "Portuguese (pt)"),
    ("pt-BR", "Portuguese (Brazil) (pt-BR)"),
    ("ru", "Russian (ru)"),
    ("ar", "Arabic (ar)"),
    ("hi", "Hindi (hi)"),
    ("bn", "Bengali (bn)"),
    ("ur", "Urdu (ur)"),
    ("fa", "Persian (fa)"),
    ("tr", "Turkish (tr)"),
    ("pl", "Polish (pl)"),
    ("nl", "Dutch (nl)"),
    ("sv", "Swedish (sv)"),
    ("no", "Norwegian (no)"),
    ("da", "Danish (da)"),
    ("fi", "Finnish (fi)"),
    ("cs", "Czech (cs)"),
    ("sk", "Slovak (sk)"),
    ("hu", "Hungarian (hu)"),
    ("ro", "Romanian (ro)"),
    ("bg", "Bulgarian (bg)"),
    ("el", "Greek (el)"),
    ("he", "Hebrew (he)"),
    ("th", "Thai (th)"),
    ("vi", "Vietnamese (vi)"),
    ("id", "Indonesian (id)"),
    ("ms", "Malay (ms)"),
    ("uk", "Ukrainian (uk)"),
    ("sr", "Serbian (sr)"),
    ("hr", "Croatian (hr)"),
    ("sl", "Slovenian (sl)"),
    ("lt", "Lithuanian (lt)"),
    ("lv", "Latvian (lv)"),
    ("et", "Estonian (et)"),
    ("sw", "Swahili (sw)"),
    ("tl", "Filipino (tl)"),
]
LANGUAGE_CODES = {code for code, _ in LANGUAGES}

DEFAULTS = {
    "engine": "google",
    "target": "zh-CN",
    "provider": "",
    "model": "",
    "endpoint": "",
    "api_key": "",
    "reasoning": "lowest",
}


def _natural_key(value: str) -> list:
    """Approximate JS Intl.Collator(numeric) for stable UI order (payload is re-sorted in Node)."""
    parts = re.split(r"(\d+)", value.casefold())
    return [(0, int(part)) if part.isdigit() else (1, part) for part in parts]


def _load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_providers() -> list[dict]:
    builtins = _load_json(BUILTIN_FILE).get("providers", [])
    catalogue = _load_json(CATALOG_FILE).get("providers", [])
    merged: dict[str, dict] = {}
    for provider in builtins:
        if not isinstance(provider, dict) or not provider.get("id"):
            continue
        models = [
            model for model in provider.get("models", [])
            if isinstance(model, dict) and model.get("id")
        ]
        merged[provider["id"]] = {
            "id": provider["id"],
            "label": provider.get("label") or provider["id"],
            "endpoint": provider.get("endpoint", ""),
            "source": "built-in",
            "models": models,
        }
    for provider in catalogue:
        if not isinstance(provider, dict) or not provider.get("id"):
            continue
        if provider["id"] in merged:
            continue
        models = [
            model for model in provider.get("models", [])
            if isinstance(model, dict) and model.get("id")
        ]
        merged[provider["id"]] = {
            "id": provider["id"],
            "label": provider.get("label") or provider["id"],
            "endpoint": provider.get("endpoint", ""),
            "source": "models.dev",
            "models": models,
        }
    merged[CUSTOM_ID] = {
        "id": CUSTOM_ID,
        "label": "Custom…",
        "endpoint": "",
        "source": "custom",
        "models": [
            {"id": "gpt-4o-mini", "label": "GPT-4o mini", "reasoningOptions": []},
            {"id": "gpt-4.1", "label": "GPT-4.1", "reasoningOptions": []},
            {"id": "deepseek-chat", "label": "DeepSeek Chat", "reasoningOptions": []},
            {"id": "qwen3", "label": "Qwen3", "reasoningOptions": []},
        ],
    }
    for provider in merged.values():
        provider["models"].sort(key=lambda model: _natural_key(model.get("label", "")))
    return sorted(
        merged.values(),
        key=lambda provider: (provider["id"] == CUSTOM_ID, _natural_key(provider["label"])),
    )


def provider_by_id(provider_id: str) -> dict | None:
    return next((provider for provider in load_providers() if provider["id"] == provider_id), None)


def provider_by_label(label: str) -> dict | None:
    return next((provider for provider in load_providers() if provider["label"] == label), None)


def normalize_target(value: object) -> str:
    """Turn the old human-readable target into a BCP-47 code without losing unknown values."""
    text = str(value or "").strip()
    if not text:
        return "zh-CN"
    if text in LANGUAGE_CODES:
        return text
    match = re.search(r"\(([^()]+)\)\s*$", text)
    if match:
        code = match.group(1).strip()
        if code in LANGUAGE_CODES:
            return code
        aliases = {"zh_CN": "zh-CN", "zh_TW": "zh-TW", "pt_BR": "pt-BR", "pt_PT": "pt"}
        if code in aliases:
            return aliases[code]
    aliases = {"zh_CN": "zh-CN", "zh_TW": "zh-TW", "pt_BR": "pt-BR"}
    return aliases.get(text, "zh-CN")


def normalize_provider(value: object) -> str:
    text = str(value or "").strip()
    if text in PLACEHOLDER_VALUES:
        return ""
    provider = provider_by_id(text) or provider_by_label(text)
    return provider["id"] if provider else ""


def normalize_model(provider_id: str, value: object) -> str:
    text = str(value or "").strip()
    if not text or text in PLACEHOLDER_VALUES:
        return ""
    provider = provider_by_id(provider_id)
    if not provider:
        return text
    for model in provider["models"]:
        if model["id"] == text or model.get("label") == text:
            return model["id"]
    return text


def normalize_reasoning(value: object) -> str:
    text = str(value or "lowest").strip()
    return text if text else "lowest"


def migrate_legacy_settings(raw: object) -> dict:
    """Read an old settings dict (labels included) and return the current shape."""
    if not isinstance(raw, dict):
        raw = {}
    provider = normalize_provider(raw.get("provider"))
    return {
        "engine": "ai" if str(raw.get("engine", "google")).lower() == "ai" else "google",
        "target": normalize_target(raw.get("target")),
        "provider": provider,
        "model": normalize_model(provider, raw.get("model")),
        "endpoint": str(raw.get("endpoint") or "").strip(),
        "api_key": str(raw.get("api_key") or ""),
        "reasoning": normalize_reasoning(raw.get("reasoning")),
    }


def load_settings(path: Path | str = SETTINGS_FILE) -> dict:
    raw = _load_json(Path(path))
    settings = dict(DEFAULTS)
    settings.update(migrate_legacy_settings(raw))
    return settings


def save_settings(settings: dict, path: Path | str = SETTINGS_FILE) -> None:
    target = Path(path)
    current = load_settings(target)
    current.update({key: settings.get(key, current[key]) for key in DEFAULTS})
    target.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def migrate_settings_file(path: Path | str = SETTINGS_FILE) -> dict:
    """Migrate the on-disk file once, keeping a .legacy.bak for rollback/debugging."""
    target = Path(path)
    raw = _load_json(target)
    migrated = migrate_legacy_settings(raw)
    if raw and raw != migrated:
        backup = target.with_suffix(target.suffix + ".legacy.bak")
        if not backup.exists():
            backup.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        save_settings(migrated, target)
    return migrated


def resolve_request_settings(raw: object, path: Path | str = SETTINGS_FILE) -> dict:
    """Merge legacy JSON-RPC request values into the current shape; request values win."""
    if not isinstance(raw, dict):
        raw = {}
    merged = dict(load_settings(path))
    merged.update(migrate_legacy_settings(raw))
    return merged


def reasoning_options(provider_id: str, model_id: str) -> list[str]:
    provider = provider_by_id(provider_id)
    if not provider:
        return []
    model = next((item for item in provider["models"] if item["id"] == model_id), None)
    return list(model.get("reasoningOptions", [])) if model else []


def resolve_reasoning(setting: str, options: list[str]) -> str:
    if setting != "lowest":
        return setting or ""
    for candidate in ("none", "minimal", "low"):
        if candidate in options:
            return candidate
    return ""


def endpoint_for(provider_id: str) -> str:
    provider = provider_by_id(provider_id)
    return provider["endpoint"] if provider else ""
