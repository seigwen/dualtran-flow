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

Create `settings.json` next to `main.py` (missing values fall back to the defaults):

```json
{
  "engine": "google",
  "target": "zh-CN",
  "endpoint": "https://api.openai.com/v1",
  "api_key": "",
  "model": "gpt-4o-mini"
}
```

## Status

- 12 unit tests (`python -m pytest`), and the JSON-RPC contract is exercised directly:
  `echo '{"method":"query","parameters":[""],"id":1}' | python main.py` returns a valid result.
- **Not yet verified inside Flow Launcher itself** — the host app is not installed here.

## Licence

MPL-2.0.
