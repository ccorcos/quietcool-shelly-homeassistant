# Home Assistant Whole House Fan Repo Spec

This document describes the desired GitHub repository for a Home Assistant whole-house-fan controller using three relay/switch entities, usually Shelly relays.

Target use case:

- Fan: QuietCool / RM WHF-style multi-speed whole house fan.
- Relay 1: master power on/off.
- Relay 2 + Relay 3: hardware speed selection network.
- Home Assistant UI should expose a single fan entity with `Low`, `Medium`, and `High`, plus a timer in hours.
- The UI should avoid exposing the raw relays to normal users.
- The software must never intentionally energize multiple speed leads at the same time.
- The hardware wiring should still provide the real safety interlock. Home Assistant logic must not be the only protection.

---

## Important electrical safety model

This project controls mains-voltage motor wiring. The software must be written conservatively, but software is not a substitute for correct wiring.

Required assumptions:

1. The fan is wired according to the manufacturer's installation documentation.
2. Relays/contactors are rated for the motor load and inrush current.
3. All mains wiring is inside a proper enclosure.
4. The two speed-selector relays are wired as a hardware interlock/truth table so that two speed taps cannot be energized at the same time.
5. Each Shelly/relay should have its boot/default state configured safely, preferably `off`.
6. During speed changes, the integration should remove master power, wait briefly, change speed relays, wait briefly, then restore master power if the fan was previously on.

---

# Recommended repo strategy

There are two viable implementation paths.

## Option A — YAML package repo

This is the fastest MVP. It is mostly a Home Assistant package file plus README instructions.

Pros:

- Very simple.
- No Python custom integration required.
- Easy to audit.
- Works with existing Shelly entities.

Cons:

- Not really HACS-installable in the normal sense.
- Users must manually copy the YAML package into `/config/packages/`.
- Configuration is edited manually in YAML.

## Option B — HACS custom integration

This is the preferred polished GitHub/HACS approach.

Pros:

- Can be added as a custom repository in HACS.
- Can be configured from the Home Assistant UI.
- Can validate entity IDs, expose proper HA entities, and provide services.
- Can store options in the config entry rather than requiring YAML edits.

Cons:

- More code.
- Requires Python custom integration structure.
- Needs testing across Home Assistant versions.

**Recommendation:** build Option B as the main product, but include Option A as a fallback/example package in the repo under `examples/package/whole_house_fan.yaml`.

---

# Desired repository name

Suggested repo name:

```text
ha-whole-house-fan-controller
```

Suggested integration domain:

```text
whole_house_fan_controller
```

Suggested HACS display name:

```text
Whole House Fan Controller
```

---

# Functional requirements

## Hardware model

The integration controls three existing Home Assistant switch entities:

```text
power_switch_entity
speed_relay_a_entity
speed_relay_b_entity
```

Example entities:

```text
switch.whf_power
switch.whf_speed_a
switch.whf_speed_b
```

The integration does not talk directly to Shelly APIs. It calls Home Assistant services against existing `switch` entities. This keeps it relay-brand-agnostic and lets it work with Shelly, Zooz, ESPHome, KNX, Z-Wave, Zigbee relays, etc.

## User-facing entities

The integration should create these entities:

```text
fan.whole_house_fan
number.whole_house_fan_run_hours
button.whole_house_fan_start_timer
sensor.whole_house_fan_timer_remaining       # optional but useful
sensor.whole_house_fan_timer_finishes_at     # optional but useful
```

The minimum required entities are:

```text
fan.whole_house_fan
number.whole_house_fan_run_hours
button.whole_house_fan_start_timer
```

## Fan behavior

The generated fan entity should support:

- On/off.
- Preset modes:
  - `Low`
  - `Medium`
  - `High`
- Optional percentage mapping:
  - Low = 33%
  - Medium = 66%
  - High = 100%

Preset mode should be the primary UI mechanism.

## Timer behavior

The generated timer controls how long the fan should run after pressing the Start Timer button.

Default behavior:

1. User selects speed on `fan.whole_house_fan`.
2. User sets `number.whole_house_fan_run_hours`, for example `4`.
3. User presses `button.whole_house_fan_start_timer`.
4. Integration applies selected speed.
5. Integration turns on master power.
6. Integration schedules turn-off after the configured hours.
7. At the end of the timer, integration turns off master power.

Timer should be cancelable by manually turning off the fan.

If fan is turned on manually through `fan.turn_on`, the timer should not automatically start unless the user calls a dedicated start-timer service or presses the timer button.

## Speed change behavior

Changing speed while the fan is off:

1. Save selected preset.
2. Apply speed relay states.
3. Leave master power off.

Changing speed while the fan is on:

1. Remember that fan was on.
2. Turn off master power relay.
3. Wait `power_off_delay`, default 2 seconds.
4. Apply speed-selector relay state.
5. Wait `speed_settle_delay`, default 1 second.
6. Turn master power relay back on.

Turning the fan on:

1. Apply current selected speed.
2. Wait `speed_settle_delay`.
3. Turn master power on.

Turning the fan off:

1. Cancel active timer, if any.
2. Turn master power off.
3. Leave speed relays in their last selected state.

Do not toggle speed relays while master power is on.

---

# Configurable speed truth table

The integration must allow user configuration of the relay states for each speed.

Default truth table:

| Speed | Relay A | Relay B |
|---|---:|---:|
| Low | off | off |
| Medium | on | off |
| High | on | on |

But users must be able to change this because their hardware interlock topology may differ.

Required config representation:

```json
{
  "Low": {
    "relay_a": false,
    "relay_b": false
  },
  "Medium": {
    "relay_a": true,
    "relay_b": false
  },
  "High": {
    "relay_a": true,
    "relay_b": true
  }
}
```

YAML equivalent for docs:

```yaml
speed_map:
  Low:
    relay_a: false
    relay_b: false
  Medium:
    relay_a: true
    relay_b: false
  High:
    relay_a: true
    relay_b: true
```

The integration should not assume the default mapping is correct for every installation.

---

# HACS custom integration implementation spec

## Repo structure

The repository should look like this:

```text
ha-whole-house-fan-controller/
  README.md
  LICENSE
  hacs.json
  custom_components/
    whole_house_fan_controller/
      __init__.py
      manifest.json
      const.py
      config_flow.py
      coordinator.py              # optional
      fan.py
      number.py
      button.py
      sensor.py                   # optional
      services.yaml               # optional
      strings.json
      translations/
        en.json
  examples/
    package/
      whole_house_fan.yaml
    dashboard/
      tile-card.yaml
  docs/
    wiring-notes.md
    troubleshooting.md
```

## `hacs.json`

Example:

```json
{
  "name": "Whole House Fan Controller",
  "content_in_root": false,
  "render_readme": true,
  "domains": ["fan", "number", "button", "sensor"],
  "homeassistant": "2024.6.0"
}
```

Check current HACS requirements before finalizing. HACS requirements can change.

## `manifest.json`

Example:

```json
{
  "domain": "whole_house_fan_controller",
  "name": "Whole House Fan Controller",
  "codeowners": ["@REPLACE_WITH_GITHUB_USERNAME"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/REPLACE_WITH_GITHUB_USERNAME/ha-whole-house-fan-controller",
  "iot_class": "local_push",
  "issue_tracker": "https://github.com/REPLACE_WITH_GITHUB_USERNAME/ha-whole-house-fan-controller/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

Since this integration controls existing HA entities rather than connecting to a cloud/device API, `iot_class` may also reasonably be `calculated`. Confirm against current Home Assistant developer docs.

## Platforms

`__init__.py` should forward config entries to:

```python
PLATFORMS = [Platform.FAN, Platform.NUMBER, Platform.BUTTON]
```

Optionally include `Platform.SENSOR` for remaining timer/finish-time display.

## Config flow fields

The config flow should ask for:

### Required

- Name, default: `Whole House Fan`
- Master power switch entity ID
- Speed relay A switch entity ID
- Speed relay B switch entity ID

### Speed map

For each speed, ask for relay A and relay B state:

- Low relay A: on/off
- Low relay B: on/off
- Medium relay A: on/off
- Medium relay B: on/off
- High relay A: on/off
- High relay B: on/off

Defaults:

```text
Low:    A off, B off
Medium: A on,  B off
High:   A on,  B on
```

### Timing

- Power-off delay before speed change, default `2.0` seconds.
- Speed-settle delay after speed relay change, default `1.0` seconds.
- Default run hours, default `4.0` hours.
- Minimum run hours, default `0.5`.
- Maximum run hours, default `12.0`.
- Run-hours step, default `0.5`.

### Options flow

All of the above should be editable later through an options flow.

## Validation

Config flow should validate:

- The three entity IDs exist.
- The three entity IDs are switch entities, or at least support `switch.turn_on` and `switch.turn_off`.
- The same entity is not selected for multiple roles.
- Speed map includes exactly `Low`, `Medium`, `High`.

Optional validation:

- Warn if two speeds have identical relay states.
- Warn if master power switch is currently unavailable.

---

# Internal integration behavior

## State storage

The integration should maintain:

```python
current_preset: str        # Low, Medium, High
run_hours: float
is_timer_active: bool
finish_time: datetime | None
cancel_callback: Callable | None
```

Prefer storing persistent state in config entry options or using Home Assistant restore mechanisms.

Recommended behavior on Home Assistant restart:

- Read actual master power switch state for fan on/off.
- Restore last selected preset if possible.
- If a timer was active before restart, either:
  - restore `finish_time` and reschedule if it is still in the future, or
  - document that active timers do not survive HA restarts in v0.1.

Better implementation: store `finish_time` in `Store` under `.storage` and restore it on startup.

## Service calls

The integration should use HA service calls:

```python
await hass.services.async_call(
    "switch",
    "turn_on",
    {"entity_id": entity_id},
    blocking=True,
)

await hass.services.async_call(
    "switch",
    "turn_off",
    {"entity_id": entity_id},
    blocking=True,
)
```

Use `asyncio.sleep()` for delays.

## Concurrency

All fan operations must be serialized with an `asyncio.Lock`.

Reason: avoid race conditions such as speed change and timer expiration happening simultaneously.

Pseudocode:

```python
async with self._lock:
    await self._set_speed_safely(...)
```

## Safe speed-change pseudocode

```python
async def async_set_preset_mode(self, preset_mode: str) -> None:
    if preset_mode not in ["Low", "Medium", "High"]:
        raise ValueError("Invalid preset mode")

    async with self._lock:
        fan_was_on = self.is_on

        self.current_preset = preset_mode

        if fan_was_on:
            await self._turn_power_off()
            await asyncio.sleep(self.power_off_delay)

        await self._apply_speed_relays(preset_mode)
        await asyncio.sleep(self.speed_settle_delay)

        if fan_was_on:
            await self._turn_power_on()

        self.async_write_ha_state()
```

## Apply speed relays pseudocode

```python
async def _apply_speed_relays(self, preset_mode: str) -> None:
    relay_a_on = self.speed_map[preset_mode]["relay_a"]
    relay_b_on = self.speed_map[preset_mode]["relay_b"]

    await self._set_switch(self.relay_a_entity, relay_a_on)
    await self._set_switch(self.relay_b_entity, relay_b_on)
```

Potential enhancement: turn both speed relays off first, then apply target state. Make this optional because some hardware truth tables may not require it, but it is usually safer.

Enhanced safe sequence:

```python
await self._set_switch(self.relay_a_entity, False)
await self._set_switch(self.relay_b_entity, False)
await asyncio.sleep(0.2)
await self._set_switch(self.relay_a_entity, relay_a_on)
await self._set_switch(self.relay_b_entity, relay_b_on)
```

Only do this while master power is off.

---

# Entity details

## Fan entity

Entity name:

```text
Whole House Fan
```

Entity class should extend Home Assistant `FanEntity`.

Supported features:

```python
FanEntityFeature.PRESET_MODE
FanEntityFeature.SET_SPEED       # optional if implementing percentage
```

Preset modes:

```python
["Low", "Medium", "High"]
```

Properties:

- `is_on`: derived from the master power switch state.
- `preset_mode`: current selected preset.
- `preset_modes`: `Low`, `Medium`, `High`.
- `percentage`: optional, maps `Low=33`, `Medium=66`, `High=100` if on; maybe `0` if off.
- `speed_count`: `3` if implementing percentage.

Methods:

- `async_turn_on(percentage=None, preset_mode=None, **kwargs)`
- `async_turn_off(**kwargs)`
- `async_set_preset_mode(preset_mode)`
- `async_set_percentage(percentage)` optional

Percentage mapping if implemented:

```python
percentage <= 33 -> Low
34..66 -> Medium
67..100 -> High
0 -> turn off
```

## Number entity

Entity:

```text
number.whole_house_fan_run_hours
```

Purpose: run duration in hours for the timer button.

Properties:

- Native min: configurable, default `0.5`.
- Native max: configurable, default `12.0`.
- Native step: configurable, default `0.5`.
- Unit: `h`.
- Mode: box or slider. HA frontend decides, but docs can recommend box.

## Button entity

Entity:

```text
button.whole_house_fan_start_timer
```

Press behavior:

1. Turn on fan at current selected preset.
2. Schedule timer using `number.whole_house_fan_run_hours`.

## Optional sensor entities

### Timer remaining

```text
sensor.whole_house_fan_timer_remaining
```

Could report minutes remaining or a human-readable duration.

Recommended unit:

```text
min
```

### Timer finishes at

```text
sensor.whole_house_fan_timer_finishes_at
```

Device class:

```text
timestamp
```

---

# Optional services

Add services to `services.yaml`.

## `whole_house_fan_controller.start_timer`

Fields:

```yaml
entity_id:
  required: true
  selector:
    entity:
      domain: fan
hours:
  required: true
  selector:
    number:
      min: 0.1
      max: 24
      step: 0.1
speed:
  required: false
  selector:
    select:
      options:
        - Low
        - Medium
        - High
```

Behavior:

- If `speed` supplied, set preset first.
- Turn on fan.
- Start timer for `hours`.

## `whole_house_fan_controller.cancel_timer`

Fields:

```yaml
entity_id:
  required: true
  selector:
    entity:
      domain: fan
```

Behavior:

- Cancel active timer.
- Does not necessarily turn fan off unless an optional `turn_off` boolean is provided.

---

# Dashboard card example

Include this in `examples/dashboard/tile-card.yaml`.

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: fan.whole_house_fan
    name: Whole House Fan
    icon: mdi:fan
    features_position: bottom
    vertical: false
    features:
      - type: fan-preset-modes
        preset_modes:
          - Low
          - Medium
          - High

  - type: entities
    title: Whole House Fan Timer
    entities:
      - entity: number.whole_house_fan_run_hours
        name: Hours
      - entity: button.whole_house_fan_start_timer
        name: Start Timer
      - entity: sensor.whole_house_fan_timer_remaining
        name: Remaining
```

If optional sensors are not implemented, remove the sensor line.

---

# Example YAML package fallback

Include this file in `examples/package/whole_house_fan.yaml` for users who do not want the HACS integration.

```yaml
input_select:
  whf_speed:
    name: Whole House Fan Speed
    options:
      - Low
      - Medium
      - High
    initial: Low
    icon: mdi:fan

input_number:
  whf_run_hours:
    name: Whole House Fan Run Time
    min: 0.5
    max: 12
    step: 0.5
    mode: box
    unit_of_measurement: h
    icon: mdi:timer-outline

timer:
  whf_run_timer:
    name: Whole House Fan Timer
    restore: true

template:
  - fan:
      - name: Whole House Fan
        unique_id: whole_house_fan_virtual
        state: "{{ is_state('switch.whf_power', 'on') }}"
        preset_mode: "{{ states('input_select.whf_speed') }}"
        preset_modes:
          - Low
          - Medium
          - High
        turn_on:
          action: script.whf_turn_on
        turn_off:
          action: script.whf_turn_off
        set_preset_mode:
          action: script.whf_set_speed
          data:
            preset_mode: "{{ preset_mode }}"

  - button:
      - name: Start Whole House Fan Timer
        unique_id: start_whole_house_fan_timer
        icon: mdi:timer-play-outline
        press:
          action: script.whf_start_timer

script:
  whf_turn_on:
    alias: Whole House Fan - Turn On
    mode: restart
    sequence:
      - action: script.whf_set_speed
        data:
          preset_mode: "{{ states('input_select.whf_speed') }}"
      - delay: "00:00:01"
      - action: switch.turn_on
        target:
          entity_id: switch.whf_power

  whf_turn_off:
    alias: Whole House Fan - Turn Off
    mode: restart
    sequence:
      - action: timer.cancel
        target:
          entity_id: timer.whf_run_timer
      - action: switch.turn_off
        target:
          entity_id: switch.whf_power

  whf_set_speed:
    alias: Whole House Fan - Set Speed
    mode: restart
    fields:
      preset_mode:
        name: Preset mode
        required: true
        example: Low
    sequence:
      - variables:
          requested_speed: "{{ preset_mode | default(states('input_select.whf_speed')) }}"
          fan_was_on: "{{ is_state('switch.whf_power', 'on') }}"
      - condition: template
        value_template: "{{ requested_speed in ['Low', 'Medium', 'High'] }}"
      - action: input_select.select_option
        target:
          entity_id: input_select.whf_speed
        data:
          option: "{{ requested_speed }}"
      - if:
          - condition: template
            value_template: "{{ fan_was_on }}"
        then:
          - action: switch.turn_off
            target:
              entity_id: switch.whf_power
          - delay: "00:00:02"
      - action: script.whf_apply_speed_only
        data:
          preset_mode: "{{ requested_speed }}"
      - delay: "00:00:01"
      - if:
          - condition: template
            value_template: "{{ fan_was_on }}"
        then:
          - action: switch.turn_on
            target:
              entity_id: switch.whf_power

  whf_apply_speed_only:
    alias: Whole House Fan - Apply Speed Relay State Only
    mode: restart
    fields:
      preset_mode:
        name: Preset mode
        required: true
        example: Low
    sequence:
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ preset_mode == 'Low' }}"
            sequence:
              - action: switch.turn_off
                target:
                  entity_id: switch.whf_speed_a
              - action: switch.turn_off
                target:
                  entity_id: switch.whf_speed_b
          - conditions:
              - condition: template
                value_template: "{{ preset_mode == 'Medium' }}"
            sequence:
              - action: switch.turn_on
                target:
                  entity_id: switch.whf_speed_a
              - action: switch.turn_off
                target:
                  entity_id: switch.whf_speed_b
          - conditions:
              - condition: template
                value_template: "{{ preset_mode == 'High' }}"
            sequence:
              - action: switch.turn_on
                target:
                  entity_id: switch.whf_speed_a
              - action: switch.turn_on
                target:
                  entity_id: switch.whf_speed_b

  whf_start_timer:
    alias: Whole House Fan - Start Timer
    mode: restart
    sequence:
      - variables:
          run_hours: "{{ states('input_number.whf_run_hours') | float(1) }}"
          total_minutes: "{{ (run_hours * 60) | round(0) | int }}"
      - action: script.whf_turn_on
      - action: timer.start
        target:
          entity_id: timer.whf_run_timer
        data:
          duration: >-
            {{ '%02d:%02d:00' | format(total_minutes // 60, total_minutes % 60) }}

automation:
  - id: whf_timer_finished_turn_off
    alias: Whole House Fan - Timer Finished Turn Off
    mode: single
    trigger:
      - platform: event
        event_type: timer.finished
        event_data:
          entity_id: timer.whf_run_timer
    action:
      - action: script.whf_turn_off
```

---

# README.md content to generate

The coding agent should create a `README.md` roughly like this.

```markdown
# Whole House Fan Controller for Home Assistant

A Home Assistant custom integration for controlling a multi-speed whole house fan using three relay/switch entities.

Typical hardware:

- One relay for master fan power.
- Two relays for speed selection.
- Hardware interlock wiring so that only one speed lead can be energized at a time.

The integration exposes a clean Home Assistant UI:

- `fan.whole_house_fan` with `Low`, `Medium`, and `High` preset modes.
- `number.whole_house_fan_run_hours` for timer duration.
- `button.whole_house_fan_start_timer` to start the fan for the selected number of hours.

## Safety warning

This integration controls mains-voltage motor wiring. Use correct wiring, proper enclosures, rated relays/contactors, and a hardware interlock. Do not rely on Home Assistant software as your only safety mechanism.

## Installation with HACS

### Add custom repository

1. Open Home Assistant.
2. Open HACS.
3. Go to the three-dot menu in the top right.
4. Choose **Custom repositories**.
5. Add this repository URL:

   ```text
   https://github.com/REPLACE_WITH_GITHUB_USERNAME/ha-whole-house-fan-controller
   ```

6. Category: **Integration**.
7. Click **Add**.
8. Search HACS for **Whole House Fan Controller**.
9. Install it.
10. Restart Home Assistant.

### Add the integration

1. Go to **Settings → Devices & services**.
2. Click **Add integration**.
3. Search for **Whole House Fan Controller**.
4. Select your three switch entities:
   - Master power switch.
   - Speed relay A.
   - Speed relay B.
5. Configure the relay truth table for Low, Medium, and High.
6. Save.

## Relay truth table

Default mapping:

| Speed | Relay A | Relay B |
|---|---:|---:|
| Low | off | off |
| Medium | on | off |
| High | on | on |

Change this to match your wiring.

## Operation

- Turning on the fan applies the selected speed, then turns on master power.
- Turning off the fan turns off master power.
- Changing speed while running turns off master power first, changes speed relays, waits briefly, then restores power.
- Pressing the timer button runs the fan for the configured number of hours.

## Dashboard example

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: fan.whole_house_fan
    name: Whole House Fan
    icon: mdi:fan
    features_position: bottom
    vertical: false
    features:
      - type: fan-preset-modes
        preset_modes:
          - Low
          - Medium
          - High

  - type: entities
    title: Whole House Fan Timer
    entities:
      - entity: number.whole_house_fan_run_hours
        name: Hours
      - entity: button.whole_house_fan_start_timer
        name: Start Timer
```

## Manual YAML package alternative

If you do not want a custom integration, see:

```text
examples/package/whole_house_fan.yaml
```

Copy it to:

```text
/config/packages/whole_house_fan.yaml
```

Then enable packages in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Restart Home Assistant.

## Troubleshooting

### The fan does not turn on

Check that the master power switch entity works from Home Assistant.

### Speed changes do not match Low/Medium/High

Your speed truth table is probably different. Edit the integration options and change the relay states for each speed.

### The fan turns off during speed changes

This is expected. The integration intentionally removes master power before switching speed relays.

### Timer disappeared after restart

Depending on implementation version, active timers may not survive Home Assistant restarts. Check the release notes.
```

---

# HACS setup instructions for maintainers

The coding agent should ensure:

1. The repo has a valid `hacs.json`.
2. The integration lives under:

   ```text
   custom_components/whole_house_fan_controller/
   ```

3. `manifest.json` contains a version.
4. GitHub releases are created with semantic versions:

   ```text
   v0.1.0
   v0.2.0
   v1.0.0
   ```

5. The README clearly says users must add the repo as a HACS custom repository of category **Integration**.

This does not need to be accepted into the default HACS store at first. Users can install it as a custom repository.

---

# Testing requirements

At minimum, test these cases in a Home Assistant dev container or test instance.

## Config flow

- Can add integration with three valid switch entities.
- Rejects duplicate entity IDs.
- Rejects non-switch entities, or warns clearly.
- Options flow can update truth table and delays.

## Fan behavior

- Turn on from off.
- Turn off from on.
- Set Low while off.
- Set Medium while off.
- Set High while off.
- Change Low → Medium while on.
- Change Medium → High while on.
- Change High → Low while on.
- Fan always turns master power off before changing speed relays.

## Timer behavior

- Start timer for 0.5 hours.
- Timer expiration turns fan off.
- Manual fan off cancels timer.
- Changing speed during active timer does not cancel timer.
- Starting timer while one is active replaces/resets timer.

## Failure behavior

- If a speed relay is unavailable, integration should not turn on master power.
- If master power turn-on fails, integration should report/raise an error and keep state consistent.
- If Home Assistant restarts, integration should recover gracefully.

---

# Implementation notes for the coding agent

- Use modern Home Assistant custom integration patterns.
- Use config entries and config flow; avoid YAML-only configuration for the custom integration.
- Serialize all operations with an `asyncio.Lock`.
- Use `blocking=True` for switch service calls so the sequence waits for each relay command.
- Do not call speed-relay changes while master power is on.
- Expose useful diagnostics or log messages, but avoid noisy logs.
- Prefer a relay-brand-agnostic implementation that controls existing HA entities.
- Keep the README non-expert-friendly but explicit about electrical safety.

---

# Nice-to-have future features

- Optional temperature-based automations are out of scope for v0.1 but could be examples later.
- Optional contactor feedback input.
- Optional damper-open sensor interlock.
- Optional outside-air temperature condition.
- Optional window-open confirmation.
- Optional Lovelace custom card.
- Optional energy sensor aggregation if Shelly power metering is available.

---

# Definition of done

A user should be able to:

1. Install the repo through HACS as a custom integration.
2. Restart Home Assistant.
3. Add the integration through the UI.
4. Select three switch entities.
5. Configure the Low/Medium/High relay truth table.
6. See a fan entity, run-hours number entity, and start-timer button.
7. Add the provided dashboard card.
8. Turn the fan on/off, change speeds, and run it for N hours without directly touching the raw Shelly entities.
