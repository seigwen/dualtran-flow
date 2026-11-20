"""Small runtime i18n loader used by the query result and the Tk settings window."""
from __future__ import annotations

import json
import locale
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCALES_DIR = HERE / "locales"
LOCALE_CODES = [
    "af", "ar", "ca", "cs", "da", "de", "el", "en", "es", "fa", "fi", "fr",
    "he", "hi", "hr", "hu", "is", "it", "ja", "ko", "lv", "nl", "no", "pl",
    "pt_BR", "pt_PT", "ro", "ru", "sl", "sr", "sv", "th", "tr", "ug", "uk",
    "vi", "zh_CN", "zh_TW",
]
DEFAULT_KEYS = {
    "settingsTitle": "DualTran",
    "engine": "Engine",
    "targetLanguage": "Target language",
    "provider": "AI provider",
    "endpoint": "API endpoint",
    "apiKey": "API key",
    "model": "Model",
    "reasoning": "Reasoning effort",
    "selectLanguage": "Select a language",
    "selectProvider": "Select a provider",
    "selectModel": "Select a model",
    "reasoningLowest": "Lowest (automatic)",
    "reasoningNone": "None",
    "reasoningMinimal": "Minimal",
    "reasoningLow": "Low",
    "reasoningMedium": "Medium",
    "reasoningHigh": "High",
    "reasoningXhigh": "XHigh",
    "reasoningMax": "Max",
    "save": "Save",
    "cancel": "Cancel",
    "settingsCommand": "DualTran: Settings",
    "settingsSubtitle": "Open the DualTran settings window",
    "translationFailed": "DualTran failed",
    "providerRequired": "Select an AI provider in settings before translating.",
    "invalidEndpoint": "Endpoint must start with http:// or https://",
    "networkError": "Cannot reach the AI service — check the API endpoint and network",
    "emptyQuery": "Type text to translate…",
    "emptyQuerySubtitle": "e.g. dt hello world",
    "settingsSaved": "Settings saved",
}


def _locale_name() -> str:
    # Flow runs beside the user's desktop; honor the OS locale but normalize to our set.
    raw = os.environ.get("LANG") or os.environ.get("LC_ALL") or ""
    if not raw:
        try:
            raw = locale.getdefaultlocale()[0] or ""
        except Exception:
            raw = ""
    raw = raw.split(".")[0].replace("-", "_")
    if raw in LOCALE_CODES:
        return raw
    aliases = {"zh": "zh_CN", "zh_cn": "zh_CN", "zh_tw": "zh_TW", "pt_br": "pt_BR", "pt_pt": "pt_PT"}
    return aliases.get(raw.lower(), "en")


def load(locale_name: str | None = None) -> dict[str, str]:
    name = locale_name or _locale_name()
    path = LOCALES_DIR / f"{name}.json"
    if not path.exists():
        path = LOCALES_DIR / "en.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return {**DEFAULT_KEYS, **{key: str(value) for key, value in data.items() if value}}


def t(key: str, locale_name: str | None = None) -> str:
    return load(locale_name).get(key, key)
