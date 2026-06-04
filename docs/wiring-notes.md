# Wiring notes

This project controls existing Home Assistant switch entities. It does not replace correct electrical design.

Required assumptions:

1. The fan is wired according to the manufacturer's installation documentation.
2. Relays/contactors are rated for the motor load and inrush current.
3. All mains wiring is inside a proper enclosure.
4. The speed-selector relays are wired with a hardware interlock or truth-table arrangement appropriate for the motor.
5. Each relay's boot/default state is configured safely, preferably off.

The integration turns off master power before changing speed relay states, but Home Assistant software must not be the only safety protection.
