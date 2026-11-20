import json

import i18n
import main


def test_all_locale_files_have_every_key():
    keys = set(i18n.DEFAULT_KEYS)
    assert len(i18n.LOCALE_CODES) == 38
    for locale in i18n.LOCALE_CODES:
        path = i18n.LOCALES_DIR / f"{locale}.json"
        assert path.exists(), locale
        messages = json.loads(path.read_text(encoding="utf-8"))
        missing = keys - set(messages)
        assert not missing, f"{locale}: {sorted(missing)}"
        assert all(str(messages[key]).strip() for key in keys)
        if locale not in {"zh_CN", "zh_TW", "ja"}:
            cjk = [key for key in keys if any("\u3400" <= char <= "\u9fff" for char in str(messages[key]))]
            assert not cjk, f"{locale}: CJK in {cjk}"


def test_empty_query_offers_settings_entry(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    results = main.query("")
    assert results[0]["IcoPath"] == "icon.png"
    assert results[1]["Title"] == i18n.t("settingsCommand")
    assert results[1]["JsonRPCAction"]["method"] == "open_settings"
