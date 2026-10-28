import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dualtran_core as core


def test_rejects_schemeless_endpoint():
    with pytest.raises(core.TranslationError, match="must start with http"):
        core.normalize_endpoint("api.openai.com/v1")


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("https://api.openai.com/v1", "https://api.openai.com/v1/chat/completions"),
        ("https://api.deepseek.com", "https://api.deepseek.com/v1/chat/completions"),
        ("https://x/api/v1/chat/completions", "https://x/api/v1/chat/completions"),
    ],
)
def test_chat_url_shapes(endpoint, expected):
    assert core.chat_completions_url(endpoint) == expected


def test_payload_names_the_target_language():
    payload = core.build_chat_payload("gpt-4o-mini", "Hello", "zh-CN")
    assert "zh-CN" in payload["messages"][0]["content"]
    assert payload["messages"][1]["content"] == "Hello"
    assert payload["temperature"] == 0


def test_parse_chat_response_reads_first_choice():
    assert core.parse_chat_response({"choices": [{"message": {"content": "你好"}}]}) == "你好"


def test_parse_chat_response_surfaces_provider_error():
    with pytest.raises(core.TranslationError, match="bad key"):
        core.parse_chat_response({"error": {"message": "bad key"}})


def test_parse_chat_response_refuses_empty():
    with pytest.raises(core.TranslationError, match="empty"):
        core.parse_chat_response({"choices": [{"message": {"content": "   "}}]})


def test_google_url_encodes_the_text():
    url = core.google_url("hello world", "zh-CN")
    assert "q=hello+world" in url and "tl=zh-CN" in url


def test_parse_google_response_joins_sentences():
    assert core.parse_google_response([[["你好", "Hello"], ["世界", " world"]], None, "en"]) == "你好世界"


def test_parse_google_response_rejects_unknown_shape():
    with pytest.raises(core.TranslationError, match="Unexpected"):
        core.parse_google_response({"nope": True})


def test_translate_rejects_blank_input():
    with pytest.raises(core.TranslationError, match="Nothing"):
        core.translate("   ", "zh-CN")
