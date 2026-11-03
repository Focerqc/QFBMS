# WP1 evidence checkpoint — November 3, 2026

This checkpoint contains investigation only. It is not a completed WP1 gate or electrical sign-off. The user subsequently requested a shorter path to reference-based schematic implementation; do not turn unresolved procurement/bench questions into a prerequisite for drafting the schematic.

## Evidence collected

- `baseline-hashes.json`: SHA-256 and size of working design files, footprint libraries, models, and supplied firmware. Re-run the read-only collector to compare against this initial manifest.
- `fixed-placement.json`: 45 connector and R_B footprints, including UUID, XY, rotation, side, pad geometry, outline and model references. Preserve these when implementing the schematic/PCB later.
- `live-board.json`: fresh direct KiCad pcbnew inspection of 150 footprints.
- `prior-inventory-comparison.json`: zero differences in pad assignments, footprint XY and rotation against exports/planning-2026-11-03/pad-inventory.json. Repeated pad numbers are preserved in the new data; the old dictionary inventory collapsed them.
- `pin-ledger.json`: all 655 physical pad instances joined to regenerated schematic XML where available. Symbol pin functions are schematic evidence, not independently verified manufacturer functions. Unassigned pads explicitly remain unresolved.
- `short-crossing-triage.json`: all 199 short reports and 60 crossing reports, with item UUIDs, positions, net names and live track/pad geometry where resolved. This is mechanical classification, not 259 individually resolved circuit decisions.
- `drc.json`: 650 violations, 146 unconnected items, 366 parity issues. The previous report had 649 violations; new type totals differ by one clearance report. Item-level comparison is in `report-comparison.json`; object ordering can cause apparent added/removed entries. Both reports describe an electrically incomplete board.
- `erc.json`: 121 violations. `schematic.xml`: fresh KiCad XML export.
- `project-rules.json`: exact project settings snapshot. Five disabled checks are recorded in report-comparison.json: missing courtyard, track not centered on via, tuning geometry, footprint filters, footprint/pad type mismatch.
- KiCad CLI emitted HKCU registry access errors but completed the report operations. No board save, zone refill, schematic import or generator was run.

## Additional verified source findings

The actual BQ values are BQ7695202. TI's locally supplied SLUSE13B device comparison table (section 5) specifies I2C with CRC and REG1 default enabled at 3.3 V for this variant. The supplied C driver reads and verifies CRC. Therefore the previous generic concern that REG1 is necessarily unavailable until software configures it must not be applied to the 02 ordering option. A valid preregulator and local supply are still necessary; a regulator default is not proof of an implemented wake circuit.

PCB_VERSION is explicitly 2 in hw_vbms32.h:47. ext_get_current returns CC2/100 without a sign reversal for that version; Lisp then multiplies by -0.2. TI section 6 states that charging produces positive SRP minus SRN. Thus a correctly oriented charging sense voltage gives negative application current. Application current = -0.2 * (R_sensed / 0.0002 ohm) * physical charge current, subject to gain/offset calibration. At 5 A, sensing 1 milliohm ideally reports -5 A; sensing both 1 milliohm resistors reports -10 A. The current PCB does not establish that pickup: R_S1/R_S2 are unassigned and the SRP/SRN nets shared between BQs are not valid Kelvin wiring. Do not infer a selected sense resistance from the two resistor labels.

The GPIO9 control is used repeatedly, not just at startup: Lisp with-com drives it low before communication and can drive it high again to save power. It also refers to CAN enabling. Upper isolation/disconnect circuitry must tolerate repeated gating without resetting the lower device address or back-powering either domain. C startup logs an address-write failure but still enables the second path; the schematic/software adaptation must require successful address verification before admitting the upper 0x08 device.

Crash handling exists: main-ctrl and balance traps set did-crash, and the re-init thread calls init-hw before bms-set-chg 0. This ordering does not establish bounded charge-off if initialization blocks or fails. Move charge-off ahead of recovery in a future maintained adaptation and establish a hardware default-off/interlock; do not claim the supplied software has no recovery code.

Both BQs currently assign pin 17 to GND and pins 18/20 to shared SRP/SRN. Upper VC0 is CELL16. Upper pins 26/27 and supply/control support are largely unassigned. All ESP32 footprint pads are unassigned. These are concrete schematic tasks, not reasons to postpone drawing verified blocks.

## Harness and visual evidence status

The wiring drawing and real top photo were opened and inspected. The wiring drawing uses a different reference-board rendering and must not be treated as a manufacturer connector numbering drawing. Current PCB assignments uniquely enumerate CELL0 through CELL32: J_CELL1 pins 1–10 = CELL9 down to CELL0; J_CELL2 pins 1–9 = CELL18 down to CELL10; J_CELL3 pins 1–8 = CELL26 down to CELL19; J_CELL4 pins 1–6 = CELL32 down to CELL27. These are verified assigned nets, not verified mating-harness continuity. Pin-key orientation comparison and independent polarity confirmation remain incomplete; no claim of passing the 33-tap gate is made.

The existing Chrome PCB dashboard at localhost:5180 was inspected. It showed the working-board selection, reference image and older 3D render, but also a persistent “Reading ... with KiCad” indication. Therefore it is not fresh connectivity evidence. The progress dashboard and native KiCad editor visual pass remain outstanding. Direct KiCad pcbnew and CLI evidence above is fresh.

## Component research status

`component-ledger.json` covers every footprint but is an identity/review ledger, not a manufacturer-approved BOM. The local photos show two R001 markings; purchased resistance/tolerance and exact shunt MPN remain unverified. Generic GSRELAY/01X/Unmarked/Schottky/TVS labels cannot establish identities.

Primary-source checks: Analog Devices describes LTC7138 as 4–140 V input, up to 400 mA (https://www.analog.com/en/products/ltc7138.html). A nominal 134 V charger leaves only 6 V below that operating ceiling; tolerance and transient protection must be designed. This is not evidence that U4's unassigned pads implement a working converter. Espressif's current module datasheet is https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html; its module pad numbering must be used instead of chip GPIO numbering. Complete manufacturer pin-by-pin, footprint and rating verification is still open.

## Next concrete implementation package

Start reference-based schematic construction without waiting for the entire BOM or bench verification to close. First implement the two 16-cell monitor sheets: connector pin identities, 32 differential cell channels, TI reference input filters and balancing, each BQ supply/decoupling, local ground and explicit unused-pin treatment. Use CELL0 for lower VSS and CELL16 for upper VSS; never propagate the existing shared upper SRP/SRN error. Preserve fixed PCB geometry and do not update PCB from the schematic yet.

Then implement a separate isolated upper communication/wake sheet compatible with GPIO9 high=disconnected and low=connected. Complete ESP32, supplies, temperature inputs, charge-voltage sensing and charge-only switch sheets in successive reviewable increments. Copy verified reference circuits; visibly mark unresolved identity/value choices instead of inventing them. A photographed original board is evidence of arrangement and markings, not a complete electrical schematic.

Before any PCB update: review the schematic netlist against the pad ledger, confirm harness polarity/keying, and compare fixed geometry hashes. Procurement, transient/thermal calculations and bench acceptance remain release gates, not barriers to starting schematic drafting.
