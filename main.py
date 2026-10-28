"""Flow Launcher entry point.

Flow Launcher talks JSON-RPC over stdin/stdout: it sends a request object and expects a single
JSON line back. The plugin translates whatever the user typed after the action keyword and
returns one result whose title is the translation; pressing Enter copies it to the clipboard.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

from dualtran_core import TranslationError, translate

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
DEFAULTS = {
    "engine": "google",
    "target": "zh-CN",
    "endpoint": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
}


def load_settings() -> dict:
    settings = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as handle:
            settings.update(json.load(handle))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return settings


def query(text: str) -> list[dict]:
    cleaned = (text or "").strip()
    if not cleaned:
        return [
            {
                "Title": "Type text to translate…",
                "SubTitle": "e.g. dt hello world",
                "IcoPath": "icon.png",
            }
        ]

    settings = load_settings()
    try:
        result = translate(
            cleaned,
            target=settings["target"],
            engine=settings["engine"],
            endpoint=settings["endpoint"],
            api_key=settings["api_key"],
            model=settings["model"],
        )
    except TranslationError as error:
        return [{"Title": "Translation failed", "SubTitle": str(error), "IcoPath": "icon.png"}]

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


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method")
        parameters = request.get("parameters") or []
        try:
            if method == "query":
                payload = query(parameters[0] if parameters else "")
            elif method == "copy_to_clipboard":
                payload = copy_to_clipboard(parameters[0] if parameters else "")
            else:
                payload = []
        except Exception:
            payload = [
                {
                    "Title": "DualTran error",
                    "SubTitle": traceback.format_exc(limit=1).strip().replace("\n", " "),
                    "IcoPath": "icon.png",
                }
            ]

        sys.stdout.write(
            json.dumps({"result": payload, "id": request.get("id")}, ensure_ascii=False) + "\n"
        )
        sys.stdout.flush()


if __name__ == "__main__":
    main()
