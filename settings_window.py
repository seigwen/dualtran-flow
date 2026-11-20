"""DualTran's Flow settings window.

Run this with pythonw.exe from the plugin (the JSON-RPC action does that), so the window has
no console. The provider combo intentionally has no selectable empty row: the empty state is a
label rendered by the closed combo; opening the list shows only real providers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import i18n
import settings_model

HERE = Path(__file__).resolve().parent


class SettingsWindow:
    def __init__(self, root: tk.Tk, settings_path: Path, locale_name: str | None = None):
        self.root = root
        self.settings_path = settings_path
        self.locale_name = locale_name or i18n._locale_name()
        self.messages = i18n.load(self.locale_name)
        self.providers = settings_model.load_providers()
        self.provider_by_label = {provider["label"]: provider for provider in self.providers}
        self.model_by_label: dict[str, dict] = {}
        self.reasoning_by_label: dict[str, str] = {}
        self.last_auto_endpoint = ""
        self.settings = settings_model.migrate_settings_file(settings_path)
        self.root.title(self.t("settingsTitle") + " Settings")
        self.root.resizable(False, False)
        self._build()
        self._load_controls()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def t(self, key: str) -> str:
        return self.messages.get(key, key)

    def _build(self):
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        self.engine = tk.StringVar()
        self.target = tk.StringVar()
        self.provider = tk.StringVar()
        self.model = tk.StringVar()
        self.endpoint = tk.StringVar()
        self.api_key = tk.StringVar()
        self.reasoning = tk.StringVar()

        ttk.Label(frame, text=self.t("engine")).grid(row=0, column=0, sticky="w", pady=4)
        self.engine_box = ttk.Combobox(frame, textvariable=self.engine, values=["Google", "AI"], state="readonly", width=38)
        self.engine_box.grid(row=0, column=1, sticky="ew", pady=4)
        self.engine_box.bind("<<ComboboxSelected>>", lambda _event: self._update_state())

        ttk.Label(frame, text=self.t("targetLanguage")).grid(row=1, column=0, sticky="w", pady=4)
        self.target_box = ttk.Combobox(
            frame,
            textvariable=self.target,
            values=[label for _, label in settings_model.LANGUAGES],
            state="readonly",
            width=38,
        )
        self.target_box.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text=self.t("provider")).grid(row=2, column=0, sticky="w", pady=4)
        self.provider_box = ttk.Combobox(
            frame,
            textvariable=self.provider,
            values=[provider["label"] for provider in self.providers],
            state="readonly",
            width=38,
        )
        self.provider_box.grid(row=2, column=1, sticky="ew", pady=4)
        self.provider_box.bind("<<ComboboxSelected>>", lambda _event: self._provider_changed())

        ttk.Label(frame, text=self.t("endpoint")).grid(row=3, column=0, sticky="w", pady=4)
        self.endpoint_entry = ttk.Entry(frame, textvariable=self.endpoint, width=41)
        self.endpoint_entry.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text=self.t("apiKey")).grid(row=4, column=0, sticky="w", pady=4)
        self.api_key_entry = ttk.Entry(frame, textvariable=self.api_key, width=41, show="*")
        self.api_key_entry.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text=self.t("model")).grid(row=5, column=0, sticky="w", pady=4)
        self.model_box = ttk.Combobox(frame, textvariable=self.model, values=[], state="readonly", width=38)
        self.model_box.grid(row=5, column=1, sticky="ew", pady=4)
        self.model_box.bind("<<ComboboxSelected>>", lambda _event: self._update_reasoning())

        ttk.Label(frame, text=self.t("reasoning")).grid(row=6, column=0, sticky="w", pady=4)
        self.reasoning_box = ttk.Combobox(frame, textvariable=self.reasoning, values=[], state="readonly", width=38)
        self.reasoning_box.grid(row=6, column=1, sticky="ew", pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text=self.t("cancel"), command=self.root.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text=self.t("save"), command=self.save).pack(side="right")

    def _load_controls(self):
        engine_label = "AI" if self.settings.get("engine") == "ai" else "Google"
        self.engine.set(engine_label)
        target_label = next((label for code, label in settings_model.LANGUAGES if code == self.settings.get("target")), "")
        if not target_label:
            target_label = self.settings.get("target", "")
            self.target_box["values"] = list(self.target_box["values"]) + [target_label]
        self.target.set(target_label)
        provider = settings_model.provider_by_id(self.settings.get("provider", ""))
        self.provider.set(provider["label"] if provider else self.t("selectProvider"))
        self._populate_models(provider, self.settings.get("model", ""))
        self.endpoint.set(self.settings.get("endpoint", ""))
        self.api_key.set(self.settings.get("api_key", ""))
        self.last_auto_endpoint = settings_model.endpoint_for(provider["id"]) if provider else ""
        self._update_state()

    def _selected_provider(self) -> dict | None:
        return self.provider_by_label.get(self.provider.get())

    def _populate_models(self, provider: dict | None, preferred: str = ""):
        self.model_by_label = {}
        if provider is None:
            self.model_box["values"] = ()
            self.model.set("")
            self.reasoning_by_label = {}
            self.reasoning_box["values"] = ()
            self.reasoning.set(self.t("reasoningLowest"))
            return
        self.model_by_label = {model["label"]: model for model in provider["models"]}
        labels = list(self.model_by_label)
        self.model_box["values"] = labels
        preferred_model = next((model for model in provider["models"] if model["id"] == preferred), None)
        self.model.set(preferred_model["label"] if preferred_model else (labels[0] if labels else ""))
        self._update_reasoning()

    def _provider_changed(self):
        provider = self._selected_provider()
        if provider is None:
            return
        if not self.endpoint.get().strip() or self.endpoint.get().strip().rstrip("/") == self.last_auto_endpoint.rstrip("/"):
            self.endpoint.set(provider["endpoint"])
            self.last_auto_endpoint = provider["endpoint"]
        self._populate_models(provider, "")
        self._update_state()

    def _update_reasoning(self):
        provider = self._selected_provider()
        model = self.model_by_label.get(self.model.get())
        options = model.get("reasoningOptions", []) if model else []
        self.reasoning_by_label = {"lowest": self.t("reasoningLowest")}
        for option in options:
            key = "reasoning" + option.replace("xhigh", "xhigh").capitalize()
            self.reasoning_by_label[option] = self.t(key)
        self.reasoning_box["values"] = list(self.reasoning_by_label.values())
        current = self.settings.get("reasoning", "lowest")
        if current not in self.reasoning_by_label:
            current = "lowest"
        self.reasoning.set(self.reasoning_by_label[current])

    def _update_state(self):
        ai = self.engine.get() == "AI"
        provider = self._selected_provider()
        self.provider_box.configure(state="readonly" if ai else "disabled")
        has_provider = provider is not None
        self.model_box.configure(state="readonly" if ai and has_provider else "disabled")
        self.reasoning_box.configure(state="readonly" if ai and has_provider else "disabled")
        self.endpoint_entry.configure(state="normal" if ai else "disabled")
        self.api_key_entry.configure(state="normal" if ai else "disabled")

    def save(self):
        provider = self._selected_provider()
        model = self.model_by_label.get(self.model.get())
        target_label = self.target.get()
        target_code = next((code for code, label in settings_model.LANGUAGES if label == target_label), target_label)
        reasoning_label = self.reasoning.get()
        reasoning = next((value for value, label in self.reasoning_by_label.items() if label == reasoning_label), "lowest")
        settings = {
            "engine": "ai" if self.engine.get() == "AI" else "google",
            "target": target_code,
            "provider": provider["id"] if provider else "",
            "model": model["id"] if model else "",
            "endpoint": self.endpoint.get().strip(),
            "api_key": self.api_key.get(),
            "reasoning": reasoning,
        }
        settings_model.save_settings(settings, self.settings_path)
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=str(settings_model.SETTINGS_FILE))
    parser.add_argument("--locale", default=None)
    args = parser.parse_args()
    try:
        root = tk.Tk()
        SettingsWindow(root, Path(args.settings), args.locale)
        root.mainloop()
    except Exception as error:
        # pythonw has no console; leave a diagnostic file next to settings.json.
        try:
            log = Path(args.settings).with_name("settings-window-error.log")
            log.write_text(str(error), encoding="utf-8")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
