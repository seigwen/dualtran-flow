# DualTran Translate for Flow Launcher

Translate whatever you type, from the launcher: `dt hello world` → the result line shows the
translation and Enter copies it.

- **Google Translate** — no key, no configuration
- **AI** — any OpenAI-compatible endpoint with your own key (OpenAI, DeepSeek, OpenRouter, a
  local Ollama). Python's `urllib` runs outside the browser, so there is no CORS wall.

## Install

1. Put this folder under `%APPDATA%\FlowLauncher\Plugins\dualtran-flow`
   (or zip it and use Flow Launcher's *Install Plugin*).
2. Make sure Python 3.9+ is on PATH.
3. Reload plugins in Flow Launcher settings; the keyword is **`dt`**.

## Configure

Settings now live in the plugin's own window:

- Type **`dt settings`** in Flow, or
- choose **DualTran: Settings** from the `dt` result list.

The window opens under `pythonw.exe` (no console), and saves `settings.json` inside the plugin
directory. The old host-rendered `SettingsTemplate.yaml` was retired because Flow's template
cannot express a non-selectable empty provider placeholder or plugin-localized settings text.
Existing settings are migrated on first launch: human-readable target labels become BCP-47
codes, the old `Select a provider` value becomes the empty provider, and model/provider/reasoning
values are preserved. A `settings.json.legacy.bak` is written before migration.

## Conformance (SPEC 2.1)

```bash
python -m pytest -q             # unit + migration + i18n tests
npm run conformance             # real settings model -> validate.mjs
npm run conformance:negative    # proves R2/R4/R5 can fail
```

The `Conformance` workflow is the required check. It reads the same `settings_model.py`,
`builtin-providers.json`, 38 locale files and `settings_window.py` used by the product, not a
hand-written passing payload.

## Status

- 22 unit/migration/i18n tests (`python -m pytest`), and the JSON-RPC contract is exercised
  directly: `python main.py '{"method":"query","parameters":[""]}'` returns the translate prompt
  plus the `DualTran: Settings` entry.
- Verified inside Flow Launcher 2.1.4 on Windows: the provider list has no selectable placeholder
  row, the Tk window saves and reopens Anthropic / Claude Opus 4.1 / endpoint without a console,
  and `dt good morning` returns `早上好`.
- Flow Launcher passes the JSON request in `argv[1]` (not stdin); the entry point accepts both
  shapes.

## Licence

MPL-2.0.
