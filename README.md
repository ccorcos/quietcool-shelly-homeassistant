# Whole House Fan Controller for Home Assistant

A small Home Assistant custom integration for controlling a multi-speed whole-house fan using three existing switch entities.

Typical hardware:

- One relay/switch for master fan power.
- Two relay/switches for speed selection.
- Hardware interlock wiring so only the intended speed lead can be energized.

The integration exposes a clean Home Assistant UI:

- `fan.whole_house_fan` with `Low`, `Medium`, and `High` preset modes.
- `number.whole_house_fan_run_hours` for timer duration.
- `button.whole_house_fan_start_timer` to start the fan for the selected number of hours.
- Optional timer sensors for remaining minutes and finish time.

No custom Lovelace card is required. Use the normal Home Assistant fan tile/card.

## Safety warning

This integration controls mains-voltage motor wiring. Use correct wiring, proper enclosures, rated relays/contactors, and a hardware interlock. Do not rely on Home Assistant software as your only safety mechanism.

The integration is conservative: when speed is changed while running, it turns the master power switch off, waits briefly, changes the speed relay states, waits briefly again, then turns master power back on. It does not intentionally change speed relays while master power is on. The default delays are 0.5 seconds each and can be changed in the integration options.

## Installation with HACS

This repository is intended to be installed as a HACS custom repository.

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

## Add the integration

1. Go to **Settings → Devices & services**.
2. Click **Add integration**.
3. Search for **Whole House Fan Controller**.
4. Select your three switch entities:
   - Master power switch.
   - Speed relay A.
   - Speed relay B.
5. Configure the relay truth table for Low, Medium, and High.
6. Configure the safety delays if desired. Defaults are 0.5 seconds after power-off and 0.5 seconds after speed relay changes.
7. Save.

## Relay truth table

Default mapping:

| Speed | Relay A | Relay B |
|---|---:|---:|
| Low | off | off |
| Medium | on | off |
| High | on | on |

Change this to match your wiring.

## Operation

- Turning on the fan applies the selected speed, waits for the speed-settle delay, then turns on master power.
- Turning off the fan turns off master power and cancels any active timer.
- Changing speed while running turns off master power first, waits for the power-off delay, changes speed relays, waits for the speed-settle delay, then restores power.
- Changing speed while off updates the speed relays but leaves master power off.
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
      - entity: sensor.whole_house_fan_timer_remaining
        name: Remaining
      - entity: sensor.whole_house_fan_timer_finishes_at
        name: Finishes At
```

See `examples/dashboard/tile-card.yaml`.

## Troubleshooting

### The fan does not turn on

Check that the master power switch entity works from Home Assistant.

### Speed changes do not match Low/Medium/High

Your speed truth table is probably different. Edit the integration options and change the relay states for each speed.

### The fan briefly turns off during speed changes

This is expected. The integration intentionally removes master power before switching speed relays.

### Do active timers survive Home Assistant restarts?

Not in v0.1. If Home Assistant restarts, start the timer again if needed.
