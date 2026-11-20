"""Flow Launcher entry point.

Flow Launcher talks JSON-RPC over stdin/stdout: it sends a request object and expects a single
JSON line back. Settings are owned by the plugin now (the host SettingsTemplate was retired);
the `DualTran: Settings` result opens the Tk window under pythonw.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback

import i18n
import settings_model
from dualtran_core import TranslationError, translate

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
DEFAULTS = settings_model.DEFAULTS


def resolve_settings(settings: dict) -> dict:
    """Normalize stored values to the contract the request layer needs."""
    resolved = dict(settings)
    resolved["target"] = settings_model.normalize_target(resolved.get("target"))
    provider_id = settings_model.normalize_provider(resolved.get("provider"))
    resolved["provider"] = provider_id
    provider = settings_model.provider_by_id(provider_id)
    if provider:
        if not str(resolved.get("endpoint") or "").strip():
            resolved["endpoint"] = provider["endpoint"]
        resolved["model"] = settings_model.normalize_model(provider_id, resolved.get("model"))
        resolved["reasoning"] = settings_model.resolve_reasoning(
            str(resolved.get("reasoning") or "lowest"),
            settings_model.reasoning_options(provider_id, resolved["model"]),
        )
    return resolved


def load_settings(overrides: dict | None = None) -> dict:
    settings = settings_model.load_settings(SETTINGS_FILE)
    if isinstance(overrides, dict):
        migrated = settings_model.migrate_legacy_settings(overrides)
        for key in DEFAULTS:
            if key in overrides:
                settings[key] = migrated[key]
    return settings


def settings_result() -> dict:
    return {
        "Title": i18n.t("settingsCommand"),
        "SubTitle": i18n.t("settingsSubtitle"),
        "IcoPath": "icon.png",
        "JsonRPCAction": {"method": "open_settings", "parameters": []},
    }


def open_settings() -> bool:
    """Spawn the Tk window with pythonw so Flow never flashes a console."""
    executable = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(executable):
        executable = sys.executable
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_window.py")
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen(
            [executable, script],
            cwd=os.path.dirname(script),
            creationflags=flags,
            close_fds=True,
        )
        return True
    except Exception:
        return False


def query(text: str, settings: dict | None = None) -> list[dict]:
    cleaned = (text or "").strip()
    if not cleaned:
        return [
            {
                "Title": i18n.t("emptyQuery"),
                "SubTitle": i18n.t("emptyQuerySubtitle"),
                "IcoPath": "icon.png",
            },
            settings_result(),
        ]
    if cleaned.lower() in {"settings", "config", "configure"}:
        return [settings_result()]

    settings = resolve_settings(settings or load_settings())
    try:
        result = translate(
            cleaned,
            target=settings["target"],
            engine=settings["engine"],
            endpoint=settings["endpoint"],
            api_key=settings["api_key"],
            model=settings["model"],
            reasoning=settings["reasoning"],
        )
    except TranslationError as error:
        return [{"Title": i18n.t("translationFailed"), "SubTitle": str(error), "IcoPath": "icon.png"}]

    return [
        {
            "Title": result,
            "SubTitle": f"{settings['target']} · {settings['engine']} · Enter to copy",
            "IcoPath": "icon.png",
            "JsonRPCAction": {"method": "copy_to_clipboard", "parameters": [result]},
        }
    ]


def copy_to_clipboard(text: str) -> bool:
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def dispatch(request: dict) -> dict:
    method = request.get("method")
    parameters = request.get("parameters") or []
    try:
        if method == "query":
            payload = query(
                parameters[0] if parameters else "",
                load_settings(request.get("settings")),
            )
        elif method == "copy_to_clipboard":
            payload = copy_to_clipboard(parameters[0] if parameters else "")
        elif method == "open_settings":
            payload = open_settings()
        else:
            payload = []
    except Exception:
        payload = [
            {
                "Title": i18n.t("translationFailed"),
                "SubTitle": traceback.format_exc(limit=1).strip().replace("\n", " "),
                "IcoPath": "icon.png",
            }
        ]
    return {"result": payload, "id": request.get("id")}


def emit(request: dict) -> None:
    sys.stdout.write(json.dumps(dispatch(request), ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    # Migrate the old host-driven settings once, before the first query reads them.
    try:
        settings_model.migrate_settings_file(SETTINGS_FILE)
    except Exception:
        pass
    # Flow Launcher launches a Python plugin with the JSON request as argv[1]
    # (not on stdin). Accept both shapes: the argv form is what the host uses,
    # the stdin form keeps the documented JSON-RPC contract and unit tests.
    if len(sys.argv) > 1 and sys.argv[1].strip().startswith("{"):
        try:
            request = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            return
        emit(request)
        return

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        emit(request)


if __name__ == "__main__":
    main()
