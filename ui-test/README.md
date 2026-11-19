# DualTran Flow Launcher UI test assets

Phase 4 black-box test assets for the real Flow Launcher desktop host.

## Host availability / version

- Flow Launcher **2.1.4** (`Flow.Launcher.exe`, portable install under
  `C:/Users/Administrator/DualTran/node/FlowLauncher/FlowLauncher/app-2.1.4`).
- Plugin **DualTran Translate 0.1.0** is installed in the host's
  `UserData/Plugins/DualTran` directory and loaded (`dt` action keyword).
- Actual hotkey from Flow's `UserData/Settings/Settings.json` is **`Alt + F1`**,
  not the documentation-default `Alt+Space`. The scenarios use the actual
  configured hotkey.

## What Flow exposes

Flow Launcher is a hotkey-invoked floating search box, not a persistent window.
The plugin's only UI is the **result row** produced for `dt <text>`:

- empty query → `Type text to translate…`, subtitle `e.g. dt hello world`;
- configured query → translated title plus subtitle `zh-CN · ai · Enter to copy`.

Flow's plugin system has **no DualTran settings UI**: `plugin.json` has no
SettingsTemplate/settings window, and there is no provider/model/endpoint/
reasoning/target dropdown to inspect. Configuration is an external
`settings.json`. The manifest therefore marks those five settings surfaces
`blocked` with the host limitation; runtime translation and the configured
target are still tested. Target-language **settings UI is not applicable**; the
target is asserted from the result subtitle (`zh-CN`) after explicit config.

## State isolation

The test uses a complete copy of `app-2.1.4` at:

```text
C:/DualTran-node/test/flow-phase4/app
```

Its `UserData` and plugin directory are independent of the user's live Flow
install. Two plugin copies were prepared from the installed plugin:

- `plugin-baseline`: `engine=google`, `target=zh-CN`, no AI key;
- `plugin-configured`: `engine=ai`, `target=zh-CN`,
  `endpoint=http://10.66.66.1:11434/v1`, `model=glm-5.3-flash:cloud`,
  `api_key=""`.

The home node reaches the VPS Ollama through a temporary TCP forwarder bound to
`10.66.66.1:11434` during the configured run; it was stopped afterwards. The
test app copy and both plugin copies were deleted after the run; the user's live
plugin folder and settings were restored/left in place.

The adapter config uses `focusOnStart: false` because Flow's window is hidden
until the hotkey opens it. Every scenario sends the actual `Alt+F1` sequence,
then types into the foreground Flow query box.

## Scenarios

| Scenario | Axis | What is asserted |
|---|---|---|
| `flow-settings-baseline` | baseline | `Alt+F1` foregrounds Flow; `dt` shows `Type text to translate…` / `e.g. dt hello world`; no raw error |
| `flow-settings-configured` | configured | `dt hello` shows Chinese `你好`; subtitle contains `zh-CN` and `ai`; no raw error |

## Run

The harness must be run while the isolated Flow copy is running. Prepare/swap
the plugin copy on the home node, launch the test app, then:

```bash
cd /root/DualTran-manage/host-ui-tests
DT_HEADLESS=1 DT_EVIDENCE_DIR=reports/phase4/flow DT_WORK_DIR=/tmp/flow-work \
  node --experimental-strip-types src/cli.ts test --host dualtran-flow --scenario flow-settings-baseline
DT_EVIDENCE_DIR=reports/phase4/flow \
  node --experimental-strip-types src/cli.ts test --host dualtran-flow --scenario flow-settings-configured
npm run ui:audit -- --host dualtran-flow
```

Evidence is under `reports/phase4/flow/`. Because the five settings surfaces
are blocked by the host's lack of a settings UI, the default audit exits **2**;
`--allow-blocked` only exempts the blocked status and does not turn them into
covered surfaces.

## Failure notes

- The first configured run failed with `Network error: [WinError 10060]` because
  the home node could not reach `10.66.66.1:11434` (Ollama on the VPS listens on
  `127.0.0.1`). A temporary TCP forwarder made the local Ollama path reachable;
  the rerun passed. This is an environment issue, not a Flow or plugin defect.
- Flow's main window has an empty `MainWindowTitle` while hidden; the driver
  asserts the foreground title `Flow.Launcher` after the hotkey before typing.
