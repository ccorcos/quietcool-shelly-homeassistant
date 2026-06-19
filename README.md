# QuietCool Shelly House Fan Controller for Home Assistant

A small Home Assistant custom integration for controlling a multi-speed whole-house fan using three existing switch entities.

Typical hardware:

- QuietCool multi-speed whole-house fan.
- Shelly 1 Gen 4 relays exposed to Home Assistant as switch entities.
- PACKARD PR372 Fan Relay for speed selection.
- One relay/switch for master fan power.
- Two relay/switches for speed selection.
- Hardware relay wiring so only the intended speed lead can be energized.

The integration exposes a clean Home Assistant UI:

- `fan.house_fan` with `Low`, `Medium`, and `High` preset modes.
- `number.house_fan_run_hours` for timer duration.
- `button.house_fan_start_timer` to start the fan for the selected number of hours.
- `switch.house_fan_timed_run` to start or stop a timed run.
- Optional timer sensors for remaining minutes and finish time.

No custom Lovelace card is required. Use the normal Home Assistant fan tile/card.

## Wiring warning

This integration is written for a Shelly 1 Gen 4 relay setup driving a PACKARD PR372 Fan Relay. Use correct wiring, proper enclosures, and rated relays/contactors so only the intended speed lead can be energized.

![](./wiring.svg)

## Installation with HACS

This repository is intended to be installed as a HACS custom repository.

1. Open Home Assistant.
2. Open HACS.
3. Go to the three-dot menu in the top right.
4. Choose **Custom repositories**.
5. Add this repository URL:

   ```text
   https://github.com/ccorcos/quietcool-shelly-homeassistant
   ```

6. Category: **Integration**.
7. Click **Add**.
8. Search HACS for **QuietCool Shelly House Fan Controller**.
9. Install it.
10. Restart Home Assistant.

## Add the integration

1. Go to **Settings → Devices & services**.
2. Click **Add integration**.
3. Search for **QuietCool Shelly House Fan Controller**.
4. Select your three switch entities:
   - Master power switch.
   - Speed relay A.
   - Speed relay B.
5. Configure the relay truth table for Low, Medium, and High.
6. Save.

## Operation

- Turning on the fan applies the selected speed relay state, then turns on master power.
- Turning off the fan turns off master power and cancels any active timer.
- Changing speed updates the speed relay state immediately. The fan stays on if it was already running.
- Changing speed while off updates the speed relays but leaves master power off.
- Pressing the timer button runs the fan for the configured number of hours.
- Turning on the timed-run switch starts a timed run; turning it off cancels the timer and turns off the fan.

## Dashboard example

Home Assistant will create the fan, timer number, timer button, and timer sensors after you add the integration. To put them together on a dashboard:

1. Open the dashboard you want to edit.
2. Click **Edit dashboard**.
3. Click **Add card**.
4. Scroll to the bottom and choose **Manual**.
5. Paste the YAML below.
6. Click **Save**.

If your entity IDs are different, replace the entity IDs in the YAML with the ones Home Assistant created for your setup.

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: fan.house_fan
    name: House Fan
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
    title: House Fan Timer
    entities:
      - entity: number.house_fan_run_hours
        name: Hours
      - entity: switch.house_fan_timed_run
        name: Timed Run
      - entity: button.house_fan_start_timer
        name: Start Timer
      - entity: sensor.house_fan_timer_remaining
        name: Remaining
      - entity: sensor.house_fan_timer_finishes_at
        name: Finishes At
```

See `examples/dashboard/tile-card.yaml`.
