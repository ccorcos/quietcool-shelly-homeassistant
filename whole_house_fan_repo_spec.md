# Home Assistant Whole House Fan Repo Spec

This document describes the repository for a Home Assistant whole-house-fan controller using three existing relay/switch entities.

Target use case:

- Fan: QuietCool / RM WHF-style multi-speed whole house fan.
- Relay 1: master power on/off.
- Relay 2 + Relay 3: hardware speed selection network.
- Home Assistant UI exposes a single fan entity with `Low`, `Medium`, and `High`, plus a timer in hours.
- The UI avoids exposing the raw relays to normal users.

---

## Repository strategy

This repo is a HACS custom integration with a YAML package fallback example.

- Main integration: `custom_components/whole_house_fan_controller/`
- YAML fallback: `examples/package/whole_house_fan.yaml`
- Dashboard example: `examples/dashboard/tile-card.yaml`
- User documentation: `README.md` and `AGENTS.md`

Repository URL:

```text
https://github.com/ccorcos/quietcool-shelly-homeassistant
```

Integration domain:

```text
whole_house_fan_controller
```

HACS display name:

```text
QuietCool Shelly Whole House Fan Controller
```

---

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

The integration does not talk directly to Shelly APIs. It calls Home Assistant services against existing `switch` entities. This keeps it relay-brand-agnostic and lets it work with Shelly, Zooz, ESPHome, KNX, Z-Wave, Zigbee relays, and similar devices.

The target hardware is Shelly 1 Gen 4 relay modules driving a PACKARD PR372 Fan Relay. The speed-selector relays are expected to be physically wired as the user's required truth table/interlock network.

---

## User-facing entities

The integration creates:

```text
fan.whole_house_fan
number.whole_house_fan_run_hours
button.whole_house_fan_start_timer
sensor.whole_house_fan_timer_remaining
sensor.whole_house_fan_timer_finishes_at
```

---

## Fan behavior

The fan entity supports:

- On/off.
- Preset modes:
  - `Low`
  - `Medium`
  - `High`
- Percentage mapping:
  - Low = 33%
  - Medium = 66%
  - High = 100%

Preset mode is the primary UI mechanism.

### Turning on

1. Apply the current selected speed relay state.
2. Turn on master power.

### Turning off

1. Cancel any active timer.
2. Turn off master power.
3. Leave speed relays in their last selected state.

### Changing speed

1. Save selected preset.
2. Apply the configured speed relay state immediately.
3. Do not cycle master power.

---

## Timer behavior

The generated timer controls how long the fan runs after pressing the Start Timer button.

Default behavior:

1. User selects speed on `fan.whole_house_fan`.
2. User sets `number.whole_house_fan_run_hours`, for example `4`.
3. User presses `button.whole_house_fan_start_timer`.
4. Integration applies selected speed.
5. Integration turns on master power.
6. Integration schedules turn-off after the configured hours.
7. At the end of the timer, integration turns off master power.

Timer should be cancelable by manually turning off the fan.

If fan is turned on manually through `fan.turn_on`, the timer should not automatically start unless the user presses the timer button.

---

## Configurable speed truth table

The integration allows user configuration of the relay states for each speed.

Default truth table:

| Speed | Relay A | Relay B |
|---|---:|---:|
| Low | off | off |
| Medium | on | off |
| High | on | on |

Users can change this to match their wiring.

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

---

## Config flow requirements

Initial setup fields:

- Name.
- Master power switch entity.
- Speed relay A switch entity.
- Speed relay B switch entity.
- Low relay A/B states.
- Medium relay A/B states.
- High relay A/B states.
- Default run hours.
- Minimum run hours.
- Maximum run hours.
- Run-hours step.

Validation:

- All three switch entities must be unique.
- All selected entities must be `switch` entities.
- Speed map must contain `Low`, `Medium`, and `High`.
- Timer min/max/default/step values must be valid.

Options flow should allow editing the same values.

---

## Implementation notes

- Shared runtime controller lives in `custom_components/whole_house_fan_controller/__init__.py`.
- Entity platforms are `fan`, `number`, `button`, and `sensor`.
- Use Home Assistant async APIs and `blocking=True` for switch service calls.
- Keep vendor-specific relay logic out of the integration.
- Keep public option keys stable unless a migration is added.

---

## Documentation requirements

- `README.md` should cover installation, setup, relay truth table, operation, and dashboard example.
- `AGENTS.md` should describe agent workflow and repo-specific implementation notes.
- `examples/dashboard/tile-card.yaml` should provide a usable dashboard card example.
- `examples/package/whole_house_fan.yaml` should mirror the integration behavior as a YAML fallback.
