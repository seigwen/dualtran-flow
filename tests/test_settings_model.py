import json
from pathlib import Path

import settings_model


def test_migrates_human_target_and_provider_placeholders():
    migrated = settings_model.migrate_legacy_settings(
        {
            "engine": "ai",
            "target": "Chinese (Simplified) (zh-CN)",
            "provider": "Select a provider",
            "model": "Select a model",
            "endpoint": "",
            "api_key": "",
            "reasoning": "lowest",
        }
    )
    assert migrated["target"] == "zh-CN"
    assert migrated["provider"] == ""
    assert migrated["model"] == ""
    assert migrated["engine"] == "ai"
    assert migrated["reasoning"] == "lowest"


def test_migrates_provider_and_model_labels_without_losing_values(tmp_path):
    old = {
        "engine": "ai",
        "target": "Japanese (ja)",
        "provider": "OpenAI",
        "model": "GPT-4.1",
        "endpoint": "https://proxy.example/v1",
        "api_key": "old-key",
        "reasoning": "high",
    }
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(old), encoding="utf-8")
    migrated = settings_model.migrate_settings_file(path)
    assert migrated["target"] == "ja"
    assert migrated["provider"] == "openai"
    assert migrated["model"] == "gpt-4.1"
    assert migrated["endpoint"] == "https://proxy.example/v1"
    assert migrated["api_key"] == "old-key"
    assert migrated["reasoning"] == "high"
    assert json.loads(path.read_text()) == migrated
    assert json.loads((tmp_path / "settings.json.legacy.bak").read_text()) == old


def test_new_settings_round_trip_and_defaults(tmp_path):
    path = tmp_path / "settings.json"
    settings_model.save_settings(
        {
            "engine": "ai",
            "target": "zh-CN",
            "provider": "openai",
            "model": "o4-mini",
            "endpoint": "https://api.openai.com/v1",
            "api_key": "test-key",
            "reasoning": "lowest",
        },
        path,
    )
    loaded = settings_model.load_settings(path)
    assert loaded["provider"] == "openai"
    assert loaded["model"] == "o4-mini"
    assert loaded["target"] == "zh-CN"
    assert settings_model.reasoning_options("openai", "o4-mini") == ["none", "minimal", "low", "medium", "high"]
    assert settings_model.resolve_reasoning("lowest", settings_model.reasoning_options("openai", "o4-mini")) == "none"


def test_request_settings_override_file(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"target": "Chinese (Traditional) (zh-TW)", "provider": "OpenAI"}), encoding="utf-8")
    assert settings_model.resolve_request_settings(
        {"target": "Japanese (ja)", "provider": "Select a provider"},
        path,
    )["target"] == "ja"
