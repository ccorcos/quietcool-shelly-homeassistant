# Troubleshooting

## Integration does not appear after HACS install

Restart Home Assistant after installing the integration from HACS.

## The setup form does not show my relay

Only `switch` entities are selectable. If your relay appears as another domain, expose or wrap it as a switch first.

## Fan does not turn on

Verify the master power switch works directly in Home Assistant.

## Speed labels are wrong

Edit the integration options and adjust the Low/Medium/High relay truth table to match your wiring.

## Fan turns off during speed changes

This is intentional. The integration turns master power off before changing speed relays, then turns it back on.

## Timer stopped after restart

Active timers are not restored after a Home Assistant restart in v0.1.
