#!/usr/bin/env python3
"""Generate the SPEC 2.1 payload from Flow's real settings model and locale resources."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import i18n  # noqa: E402
import settings_model  # noqa: E402


def message_files() -> dict[str, dict[str, str]]:
    files: dict[str, dict[str, str]] = {}
    for locale in i18n.LOCALE_CODES:
        files[locale] = i18n.load(locale)
    return files


def build() -> dict:
    providers = settings_model.load_providers()
    selected = next(
        (provider for provider in providers if provider["source"] == "built-in" and provider["models"]),
        next(provider for provider in providers if provider["models"]),
    )
    selected_model = next(
        (model for model in selected["models"] if model.get("reasoningOptions")),
        selected["models"][0],
    )
    return {
        "spec": "2.1.0",
        "host": "dualtran-flow",
        "language": {
            "control": "dropdown",
            "current": "zh-CN",
            "options": [{"value": code, "label": label} for code, label in settings_model.LANGUAGES],
        },
        "provider": {
            "control": "dropdown",
            "current": selected["id"],
            "placeholder": {
                "value": "",
                "label": "Select a provider",
                "disabled": True,
                "selected": False,
            },
            "fallback": "",
            "options": [
                {"value": provider["id"], "label": provider["label"], "source": provider["source"]}
                for provider in providers
            ],
        },
        "model": {
            "control": "dropdown",
            "disabled": False,
            "selectedProvider": selected["id"],
            "selectedModel": selected_model["id"],
            "options": [
                {"value": model["id"], "label": model["label"], "reasoningOptions": model.get("reasoningOptions", [])}
                for model in selected["models"]
            ],
            "byProvider": {
                provider["id"]: [
                    {"value": model["id"], "label": model["label"], "reasoningOptions": model.get("reasoningOptions", [])}
                    for model in provider["models"]
                ]
                for provider in providers
            },
        },
        "endpoint": {
            "control": "text",
            "current": selected["endpoint"],
            "placeholder": "https://",
            "autofill": {
                "provider": selected["id"],
                "providerApi": selected["endpoint"],
                "before": "",
                "after": selected["endpoint"],
                "userEdited": "https://proxy.example/v1",
                "afterSwitch": "https://proxy.example/v1",
            },
        },
        "reasoning": {
            "control": "dropdown",
            "disabled": False,
            "default": "lowest",
            "resolved": {
                "none": [{"setting": "lowest", "options": ["none", "minimal", "low"], "value": "none"}],
                "minimal": [{"setting": "lowest", "options": ["minimal", "low"], "value": "minimal"}],
                "low": [{"setting": "lowest", "options": ["low", "medium"], "value": "low"}],
                "none-declared": [{"setting": "lowest", "options": [], "value": ""}],
            },
        },
        "i18n": {
            "locales": i18n.LOCALE_CODES,
            "keys": list(i18n.DEFAULT_KEYS),
            "sourceLocale": "en",
            "files": message_files(),
            "used": list(i18n.DEFAULT_KEYS),
        },
    }


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False))
