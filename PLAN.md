# QFBMS build plan

Current intent agreed on November 2, 2026. This is the active plan; it supersedes the electrical proposals and finish instructions in `docs/history/`.

## Build objective

Build a 32s **charge-only** BMS around two BQ76952 monitors and an ESP32-C3-MINI-1, using the supplied VBMS32-target VESC Express firmware and VBMS32 Micro package as the intended software baseline.

The board must measure all 32 cells, read the required temperatures, measure charging current, switch charging, and balance cells. It should support the existing connector functions, communications, programming, and wake/sleep behavior needed by that software. Discharge protection is outside scope; an old `DSG`, `PACK`, or `Q2` label does not establish a discharge-protection requirement or a verified component role.

## Placement contract

- Keep the existing connector positions and mating orientations.
- Keep balance/heatsink-related capacitors, resistors, and their thermal arrangement in place. Preserve R_B1–R_B33. Identify the remaining affected references from the board and photos before moving nearby parts.
- Keep U_BQ1 and U_BQ2 in approximately their current regions. Limited local movement is acceptable; wholesale relocation is not the intended design.
- Adapt supporting circuitry to TI's applicable requirements within those constraints. Required support parts, values, and local layout can be corrected as part of electrical work; the old blanket instruction to use only existing footprints is superseded.
- Keep the existing front-side component target. C_F1–C_F32 are recorded as a back-side exception; establish their intended front-side sites and distinguish these input-filter capacitors from the mechanically fixed balance components before changing them.

See [Design rules](DESIGN_RULES.md) for the editing details.

## Architecture and sources

U_BQ1 covers the lower 16 cells and U_BQ2 the upper 16. Their local voltage references differ. Design the communication, power, wake, and control interfaces for that stacked arrangement using [TI's guidance](_reference/ti_bq76952/README.md).

The package's LispBM application runs on the ESP32, makes charging/balancing decisions, and calls the board-specific C firmware. That firmware communicates with the BQ monitors over I2C and drives charge-control GPIOs. The supplied implementation already defines charging limits, balancing policy, GPIO assignments, monitor startup, and sensing conversions. Start with the [firmware interface notes](docs/FIRMWARE_INTERFACE.md) and linked source rather than redefining those behaviors from memory.

Use the sources for their respective purposes:

- This plan and [Design rules](DESIGN_RULES.md): product intent and mechanical constraints.
- Supplied firmware/package: desired software behavior and hardware interface.
- TI documentation and component datasheets: electrical requirements, ratings, pin functions, and layout guidance.
- Working PCB and photographs: existing placement, footprints, and actual connectivity.

Resolve conflicts explicitly. An existing pad net is evidence of the current board, not proof of a correct circuit. An EVM value is an example, not automatically the value compatible with this package.

## Work sequence

### 1. Establish the hardware/software mapping

- [x] Record the charge-only scope and placement constraints.
- [x] Locate and inspect the supplied package's charge/balance logic and the firmware's interface. Both expect BMS API version 6.
- [ ] Map each connector and mechanically fixed balance/heatsink part to its actual board references and pads.
- [ ] Map the firmware's GPIOs, BQ functions, communication-enable sequence, temperature channels, and analog inputs to the PCB.
- [ ] Reconcile current-sense polarity and scale, voltage-divider ratios, and thermistor wiring with the complete firmware-plus-package conversion chain.

Deliverable: a checked circuit-to-software mapping, with specific mismatches or unknown component functions called out by reference and pin. This mapping precedes routing.

### 2. Complete the charge-only circuit

- [ ] Establish the two monitor domains and the upper monitor's communication interface, including power and startup behavior.
- [ ] Complete the cell-input filters, balancing circuit, monitor supplies, decoupling, sensing, and temperature interfaces using applicable TI guidance.
- [ ] Identify the actual function and pinout of the placed FETs and gate-control parts. Implement the package's charge-enable behavior through the required external circuit.
- [ ] Complete ESP32 power, reset/programming, CAN, enable/wake, and other package-required support circuits within the existing connector arrangement.
- [ ] Record required support-part additions or value changes and reconcile the schematic with the intended circuit without overwriting existing PCB work blindly.

Deliverable: a coherent charge-only schematic and PCB net assignment that implement the verified interface. Any unavoidable change to a fixed mechanical feature must be raised with a concrete proposed change.

### 3. Place and route

- [ ] Resolve the front-side filter-capacitor placement against the photos and the fixed thermal arrangement.
- [ ] Fit supporting parts and make only the necessary local monitor adjustments.
- [ ] Route the verified circuit with appropriate clearances, return paths, sensing connections, and thermal provisions.
- [ ] Check the preserved connector and heatsink geometry, reconcile schematic/PCB connectivity, and resolve or document justified ERC/DRC exceptions.
- [ ] Update dashboard expectations where they encode superseded discharge or topology assumptions; use dashboards as connectivity aids.

Deliverable: the routed board and matching schematic, with the mechanical constraints preserved and electrical checks recorded.

### 4. Bring up the board and verify compatibility

- [ ] Verify supplies, both monitors' startup/communication, and all cell and temperature channels using controlled bench conditions.
- [ ] Verify charging-current polarity and calibration and charger-voltage sensing against measurements.
- [ ] Verify charge enable/disable, the package's voltage/temperature/current cutoff behavior, balancing limits, and communications-failure/recovery behavior.
- [ ] Verify sleep/wake, charger detection, CAN reporting, and package/firmware compatibility on the actual hardware.
- [ ] Record the firmware/package revisions and configured limits used for the checks, then regenerate release outputs from the checked design.

Deliverable: evidence that the intended software works with this board. Source-code agreement and a clean connectivity dashboard alone do not complete bring-up.

## Current open items

These are implementation checks, not requests to invent new charging policy:

- Exact reference list for all mechanically fixed balance/heatsink components, beyond the known R_B row.
- Front-side sites for the input-filter capacitors currently recorded on the back.
- Actual circuit roles and verified pinouts for the placed charge-switch/gate-control parts.
- PCB implementation of the upper monitor interface and the firmware's switched-communication startup.
- Sensing, bias, and calibration agreement between the PCB and supplied software.

This documentation update does not change the PCB, schematic, firmware, package, or saved connectivity snapshot. Update this plan as those implementation checks are completed.
