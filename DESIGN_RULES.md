# QFBMS design and editing rules

Use [PLAN.md](PLAN.md) for the active build objective: a 32s charge-only BMS using two BQ76952 monitors and an ESP32 running the supplied VBMS32-compatible firmware/package. Discharge protection is outside scope. These rules replace the old blanket placement locks and discharge-switching proposals.

## Mechanical constraints

- Preserve the existing connectors' positions, orientation, and mating geometry. Check against `_reference/user_photos/` and the harness reference.
- Preserve the bleed-resistor row R_B1–R_B33 in its existing positions so the board can share the same case. There is no heatsink. Do not infer additional fixed capacitor/resistor positions from an assumed heatsink arrangement. An unnetted part is not expendable.
- Keep U_BQ1 and U_BQ2 in approximately their existing areas. Modest local movement is permitted for the electrical layout; do not use that flexibility to move connectors or the fixed bleed resistors.
- Supporting parts may be added, changed, or locally repositioned when justified by TI requirements and the verified software interface during electrical work. Record the reference, value/function, and reason. Do not preserve a wrong value or omit a necessary part solely because an old prompt froze every footprint.
- Maintain the front-side component target. C_F1–C_F32 are a known unresolved back-side exception. Establish their front-side sites, clear of packages and the fixed bleed-resistor row. Documentation and repository maintenance do not authorize moving them.
- If a fixed connector or bleed-resistor position must change, present the specific reference and proposed change to the user. Ordinary supporting-circuit work within the agreed constraints does not require repeated placement approval.

## Electrical and software basis

- Use TI's applicable monitor and stacked-monitor guidance for electrical design. EVM examples do not override the charge-only scope or the verified firmware interface.
- Read [docs/FIRMWARE_INTERFACE.md](docs/FIRMWARE_INTERFACE.md) and the supplied source before assigning GPIOs, BQ multifunction pins, charge control, or sensing values.
- The package runs charging/balancing policy on the ESP32. The firmware's disabled BQ automatic-protection groups do not imply that the package lacks charge limits.
- Verify the upper monitor's voltage domain and communication interface. Do not directly join signals across monitor domains based on old net labels.
- Confirm FET and gate-control component pinouts and actual circuit functions. Names such as Q2 or DSG are not evidence that discharge protection belongs in the design.
- Preserve supplied reference source for traceability; record deliberate compatibility adaptations separately from the original reference.

## Working files and verification

- The working board is `qfbms32.kicad_pcb`. Its pad nets describe current work; they are not electrical sign-off.
- Reconcile the incomplete schematic deliberately. Do not overwrite PCB work by importing an unverified netlist or running historical board generators.
- Record circuit changes and unresolved parts by reference and pin. Use ERC/DRC, mechanical checks, and staged functional verification appropriate to the change.
- Dashboard scores and the saved connectivity snapshot are aids only. Their expectations may reflect the superseded topology.
- Files in `docs/history/` are preserved evidence, not active instructions. Follow the current plan and these rules when they disagree with those files.

## Capacitor placement clarification — November 3, 2026

The user measured the reference capacitor bodies as 1.6 × 0.8 mm (0603 / 1608 metric). Use compact reflow footprints, normally `Capacitor_SMD:C_0603_1608Metric`, rather than enlarged hand-soldering variants, where electrical ratings and effective capacitance permit.

The 45 marked locations in [the placement reference](docs/capacitor-placement-reference-2026-11-03.json) are visual references only, not verified circuit identities or net assignments. Establish capacitor functions, values, voltage ratings, and domain references from TI requirements and the supplied firmware before assigning parts to those sites. Complete the electrical schematic before placement and routing. Preserve connector and bleed-resistor positions for case compatibility; there is no heatsink.
