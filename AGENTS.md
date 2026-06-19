# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project overview

This repo contains a Home Assistant custom integration for a QuietCool whole-house fan controller using Shelly 1 Gen 4 relays and a PACKARD PR372 Fan Relay.

- Integration domain: `whole_house_fan_controller`
- Custom component path: `custom_components/whole_house_fan_controller/`
- Primary UI entities:
  - `fan.house_fan`
  - `number.house_fan_run_hours`
  - `button.house_fan_start_timer`
  - `switch.house_fan_timed_run`
  - timer sensors for remaining time and finish time
- Example/non-primary artifacts:
  - `examples/dashboard/tile-card.yaml`
  - `examples/dashboard/custom-card.yaml`

Repository URL: https://github.com/ccorcos/quietcool-shelly-homeassistant

The integration controls three existing Home Assistant `switch` entities: one master power switch and two speed-selection relays.

## Relay behavior

This project controls a QuietCool whole-house fan through existing Home Assistant switch entities from Shelly 1 Gen 4 relays. The speed-selector relays are expected to drive a PACKARD PR372 Fan Relay with the appropriate truth-table arrangement for the motor.

Expected integration behavior:

1. Turning on the fan applies the selected speed relay state, then turns on master power.
2. Changing speed applies the configured speed relay state immediately; master power is not cycled by the integration.
3. Turning the fan off cancels active timers and turns off only master power; speed relays stay in the last selected state.
4. Software should remain a thin controller over the user's existing hardware wiring and should not implement timing-based relay interlocks.

When adding features, prefer clear failures: fail loudly, avoid unexpected relay activation, and do not hide Home Assistant service-call errors.

## Repository layout

```text
custom_components/whole_house_fan_controller/
  __init__.py       Runtime controller and setup/unload logic
  config_flow.py    UI config flow and options flow
  const.py          Domain, option names, defaults, presets
  entity.py         Shared base entity
  fan.py            Fan entity
  number.py         Timer duration number entity
  button.py         Start timer button entity
  sensor.py         Timer sensors
  switch.py         Timed-run switch entity
  manifest.json     Home Assistant integration metadata

custom_components/whole_house_fan_controller/www/
  quietcool-house-fan-card.js
                    Bundled compact Lovelace card
examples/           Dashboard card examples
README.md           Main user documentation
hacs.json           HACS metadata
```

## Coding guidelines

- Follow Home Assistant custom integration conventions.
- Keep async code non-blocking; use Home Assistant async APIs.
- Do not introduce direct Shelly APIs. Shelly 1 Gen 4 relays should be represented as existing Home Assistant `switch` entities.
- Keep constants in `const.py` and avoid duplicating string literals across modules.
- Entity changes should use the shared `WholeHouseFanController` where possible so all entities stay synchronized.
- Update `strings.json` when config-flow fields, errors, or entity names change.
- Update `README.md` and relevant files under `examples/` for user-visible behavior changes.
- Keep HACS/Home Assistant metadata in `manifest.json` and `hacs.json` consistent with supported platforms.

## Validation and testing

Before finishing changes:

1. Run the test suite when `pytest` is available:

   ```bash
   pytest
   ```

2. Run a syntax check for the integration:

   ```bash
   python3 -m compileall custom_components/whole_house_fan_controller
   ```

3. If Home Assistant dev dependencies are available in the environment, run any applicable Home Assistant validation/tests.
4. Manually inspect config-flow changes for selector/schema validity and matching translations in `strings.json`.

## Documentation expectations

For user-facing changes, update documentation in the same change set. In this repo, "docs" means `README.md` and `AGENTS.md`; there is intentionally no `docs/` directory.

- Installation/configuration changes: update `README.md`.
- Agent workflow or architecture changes: update `AGENTS.md`.
- Dashboard/entity examples: update files under `examples/`.
- Lovelace card changes: update `custom_components/whole_house_fan_controller/www/quietcool-house-fan-card.js` and the README resource/card instructions.

## Release/HACS notes

- Keep `custom_components/whole_house_fan_controller/manifest.json` `version` accurate for releases.
- Keep `hacs.json` domain/platform metadata aligned with actual entities.
- Repository URL: https://github.com/ccorcos/quietcool-shelly-homeassistant

## Agent workflow notes

- Check `git status --short` before and after edits.
- Prefer small, targeted edits.
- Do not make unrelated formatting-only changes.
- Preserve existing public entity names and option keys unless a migration plan is included.
