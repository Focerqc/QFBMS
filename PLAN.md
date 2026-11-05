# QFBMS completion plan

Updated November 3, 2026. Investigation and planning only. Hardware is incomplete and must not be fabricated from the present files.

## Objective and placement contract

Complete a 32s charge-only BMS with two BQ76952 monitors and ESP32-C3-MINI-1, using the supplied VBMS32 firmware and Micro package (API 6, package 1.0.4). Discharge protection is outside scope. Preserve connector coordinates, orientations and mating geometry and R_B1–R_B33 positions for the existing case. There is no heatsink. Keep both monitors near their current regions; supporting parts can change when justified. Complete the electrical schematic before final placement or routing. Never run historical generators or import an unchecked netlist.

## Evidence established in this investigation

Direct KiCad 10 pcbnew inspection finds 150 footprints. The full reference/value/footprint/position/pad-net inventory is in `exports/planning-2026-11-03/pad-inventory.json`. This is a pad assignment inventory, not proof of physical connectivity. Reports are generated evidence under ignored exports; retain them with any design review archive.

KiCad CLI DRC succeeded with Windows registry access outside the restricted sandbox. Command: `kicad-cli pcb drc --format json --all-track-errors --schematic-parity --severity-all --output exports/planning-2026-11-03/drc.json qfbms32.kicad_pcb`. No refill/save option was used. Results: 649 violations, 146 unconnected items, 366 schematic parity issues. Violation types: 199 shorting_items, 60 tracks_crossing, 28 clearance, 195 solder_mask_bridge, 56 drill_out_of_range, 23 courtyards_overlap, 15 hole_clearance, 4 copper_edge_clearance, 1 lib_footprint_mismatch and 68 text/silkscreen issues. Counts can overlap in physical cause; they are not unique defect counts. Five checks are listed as ignored in the JSON and must be reviewed before sign-off. The earlier 20 horizontal-overlap pairs are therefore not a complete defect inventory; their exact coordinate count has not been independently reproduced here.

Schematic ERC completed with 121 violations (`erc.json`); schematic netlist export is `schematic.net` in the same directory. The working schematic and board are not reconciled. `qfbms32-charge-only-draft.kicad_sch` contains functional text with no electrical symbol library; its obsolete heatsink sentence has no authority.

Verified board assignments:

- U_BQ1 at (87.875,13.875) mm and U_BQ2 at (44.775,13.875) mm both have pin 17 on GND and pins 18/20 on shared SRP/SRN. Upper pin 16 is CELL16. This is incompatible with a correctly referenced upper domain; simply correcting VSS alone is insufficient. Both exposed-pad assignments and many supply/interface/control pins are empty.
- J_CELL1 pins 1–10 carry CELL9 down to CELL0; J_CELL2 pins 1–9 carry CELL18 down to CELL10; J_CELL3 pins 1–8 carry CELL26 down to CELL19; J_CELL4 pins 1–6 carry CELL32 down to CELL27. Their value labels respectively say 0–8, 9–16, 17–24, 25–32 and are misleading. These are verified PCB assignments; mating-harness polarity remains to be checked visually and by continuity.
- R_SH1 and R_SH2 each say R001 and are assigned in series: CELL0–SHUNT_MID–CHG-. If the values represent 1 mΩ parts, the assigned chain is 2 mΩ. Actual purchased resistance and sense pickup remain unverified.
- Q1/Q2 say AGM15T03LL, custom TOLL footprints: pad 1 gate, pads 2–8 CHG+ / PACK+, drain pad D CELL32_FUSED. This records the footprint convention, not verification against the manufacturer drawing or proof of switch function.
- U4 says LTC7138 but all numbered pads are unassigned. U7 says ISO1050 DUB-8 and has logic/CAN domain assignments; no complete powered circuit is established by those assignments. U_SSR1 says GSRELAY; that marking does not establish an H2440 identity or a valid driver.

The supplied TI datasheet, EVM guide and TIDA-010208 PDFs were text-extracted for investigation; the local AGM manufacturer-branded `agm_ds.pdf` states 150 V VDS and ±20 V VGS. The file named `AGM15T03LL.pdf` is only a JavaScript website message, not a usable datasheet. At an illustrative 4.21 V/cell, pack voltage is 134.72 V, leaving only 15.28 V below a 150 V absolute rating before transients; retaining these FETs requires a documented transient/clamp margin analysis. No current rating from a cold-case datasheet establishes capability in this case without a heatsink.

Primary sources: [TI BQ76952 datasheet](https://www.ti.com/lit/ds/symlink/bq76952.pdf), local EVM section 5.4 and BOM section 5.2, [TI stacked-monitor guidance](https://www.ti.com/lit/pdf/sszt191). TI describes upper-bus isolation, separate wake requirements and domain load balancing; its switch example does not change charge-only scope. Exact component MPNs, all footprint pinouts and operating ratings remain review gates, not completed verification.

## Ordered work packages and release gates

### WP1 — Freeze evidence and resolve electrical inputs

Dependency: none. First executable package: archive hashes of working PCB, schematic, project, footprints and supplied software; save every connector and R_B footprint UUID, XY, rotation, side and pad geometry from the live board. Preserve existing user edits. Create a pin-level connection ledger from the exported netlist and pad inventory, with intended function, domain, reference pin, value, source and disposition for every pad. Classify the 199 short reports and 60 crossings by actual copper objects and coordinates. Record the five ignored DRC checks and project clearance/stackup settings.

Open the PCB dashboard on port 5180 and progress dashboard on 5181 using the README commands. Visually compare the board, harness drawing, top/bottom photographs and capacitor annotations alongside KiCad; capture views with filenames and dates. Dashboard inspection was not completed during this investigation and must not be represented as verified evidence. Reconcile harness pin numbers from the mating side, including connector keying, before relabeling anything. Do not use a score as acceptance.

Deliverables: immutable placement baseline, complete pin ledger, defect triage, harness drawing annotated by PCB pin number, requirements envelope. Pass: all 33 taps uniquely mapped with independently checked polarity; every unknown explicitly owned; no hardware edits in this package. Fail: relying on value labels, photo marks or historical net maps alone.

### WP2 — Decide architecture and component ratings

Dependency: WP1. Lower domain uses CELL0 reference and cells 1–16; upper domain uses CELL16 reference and cells 17–32. Establish separate upper VSS, exposed pad, supply returns, input capacitors, regulator decoupling, unused-pin terminations, current inputs, wake and communication. Never share lower SRP/SRN with the upper monitor. Terminate unused upper current inputs exactly as TI specifies for the chosen measurement mode. Audit BAT, REGIN/BREG, REG18/REG1/REG2, CP1, PACK/LD, RST_SHUT, TS2 and every multifunction pin against the actual ordering option and startup defaults.

Current separate-project implementation uses the ISO1640 8-D pin map and a TI TMUX154EDGSR host-side two-line switch. Its DGS map, powered-off I/O, signal range, active-low enable and GPIO9 high=open / low=connected behavior are documented in `docs/bq-disconnect-2026-11-03.md`. The firmware adaptation requires lower-address 0x10 verification before GPIO9 low can connect upper 0x08, and all repeated Lisp GPIO9 requests pass through the same C guard. Pull-up resistances, rail bounds/sequencing, aggregate current, bus loading/rise time and lower-BQ back-power behavior remain OPEN; schematic selection is not electrical or bench sign-off. Both monitors still need a wake path that operates before their configured regulator outputs are available; verify shutdown versus deep-sleep behavior separately.

Draw the charge-current loop explicitly through connector, fuse, switch and shunt, including body diodes and reverse charger conditions. Decide whether Q2 has a justified charge-only function or is legacy circuitry. Select gate driver supply, VGS clamp, gate resistor, discharge resistor and default-off behavior from actual ratings; GPIO5/10 must control the resulting truth table. Output/precharge API calls must remain harmless in the charge-only hardware or receive documented software adaptations. No unintended USB, CAN or chassis path may bypass the shunt or off-state charge switch.

Verify full-pack and half-pack supply envelopes, start voltage, quiescent current, dissipation and wake behavior. Do not connect an unverified LTC7138 circuit across the full 32s pack. Establish 3.3 V peak load capacity for ESP32, CAN-side power source and isolation reference, USB VBUS protection/backfeed prevention, CC resistors, native USB GPIO18/19, EN/reset and boot/program access. Confirm ESP32 module pad numbers from Espressif's module datasheet. Check CAN transceiver exact suffix, logic levels, isolated-side supply, termination, ESD and creepage from TI's ISO1050 datasheet.

Deliverables: reviewed domain schematic, power budget, switch-state matrix, exact-MPN BOM with manufacturer PDF revision/page, footprint pad comparison and voltage/current/thermal derating. Reject ambiguous GSRELAY, 01X, Unmarked and generic diode/TVS identities until resolved or replaced. Pass: every component meets the selected envelope and no domain crossing lacks a rated interface. Unsupported identities remain blocked decisions.

### WP3 — Close the complete software measurement chain

Dependency: WP2 sensing topology. Source details are in `docs/FIRMWARE_INTERFACE.md` and supplied C/header/Lisp files; preserve originals and put adaptations in a separate maintained target.

C assumes 0.2 mΩ, sets CC gain to 7.4768/(Rshunt×1000), reads CC2/100 and applies PCB_VERSION sign. Lisp applies −0.2 afterward and considers negative application current charging. Consequently, assuming ideal calibration, application magnitude is 0.2×Ractual/0.2mΩ times real current. A 1 mΩ sensed resistance cancels that multiplier; a sensed 2 mΩ gives twice the real magnitude. This is a derived diagnostic, not permission to choose a pickup blindly. Trace SRP/SRN to actual Kelvin points, determine PCB_VERSION, document sign, choose effective resistance and consolidate calibration intentionally. Verify offset, gain, Ah/Wh accumulation and cutoff using known injected currents.

ADC scale is (220k+4.7k)/4.7k = 47.8085. At 134.72 V the divider output would be about 2.818 V. Verify ESP32 ADC attenuation, characterized range, input protection and resistor working voltage/power; use series high-side resistors as necessary. Match charger/output pickup references and avoid switched-ground errors. Check both channels against independent voltmeters over the required range.

Firmware configures TS1, TS3, ALERT, DCHG and HDQ with internal 18 kΩ pull-up; conversion assumes 10 kΩ beta3380 NTC and subtracts 500 Ω series resistance. Package uses up to four lower-BQ cell sensors and HDQ for MOS temperature; upper external TS4 assignment is not automatically consumed. Specify actual NTC MPNs, series resistance and connector mapping, open/short handling and sensor placement. Zero configured sensors substitutes 24 °C and must not count as valid protection.

Review C initial outputs (switch controls low, COM high), GPIO3 buzzer, GPIO2 button/wake, GPIO4/8 legacy outputs, GPIO5 charge and GPIO10 power enable. `firmware/qfbms32-adaptation/` contains the separate GPIO9 lower-address gate and Lisp call-site adaptation; supplied source remains unchanged. Continue reviewing startup, crash recovery, watchdog, stale data and communication exceptions. Baseline disables automatic protection groups A/B and uses host balancing; prove a bounded charge-off response to stopped/crashed firmware and loss of either BQ. Add hardware timeout/interlock or explicit software changes where necessary; source agreement alone is insufficient.

Deliverables: signed conversion equations, pin-to-module-pad map, adaptation list, startup/fault timing requirements and configuration export. Pass: measured sign/scale and charge truth table agree at every layer; no unconsumed required sensor or undefined boot state.

### WP4 — Complete pin-level schematic and reconcile PCB

Dependencies: WP2–3. Use sheets for harness/filters/balance, lower BQ, upper BQ/isolation, supplies/ESP32, charge switch/shunt and CAN/USB. Specify every pin, decoupler, test point, pull resistor and intentional no-connect. Compare EVM examples against stacked application and firmware. Choose internal versus external balancing with calculations for current, resistor power, BQ input current and thermal limits. The fixed 33 R_B sites do not establish a 33-cell topology; identify each role without moving them. An unnetted R_B pad can still collide with copper.

Deliverables: complete schematic, ERC report, reviewed netlist diff and support-part change log. Reconcile UUID/reference associations and apply only reviewed net changes to a saved board copy first; compare fixed geometry before accepting changes into the working board. Pass: zero unexplained ERC errors and zero unexplained schematic parity issues, with every intentional exception justified by datasheet. No routing work may hide incomplete circuitry.

### WP5 — Place, route and verify mechanics

Dependency: WP4. Assign the 45 JSON capacitor marks only after their circuit roles are defined. Use compact 0603/1608 reflow footprints where voltage rating, DC-bias effective capacitance, tolerance and temperature permit. Marks are visual locations, not identities. Resolve C_F1–C_F32 back-side placement against front-side target; place differential cell filters and supply decoupling close to their respective pins with short local returns. Keep upper returns out of lower ground. Reserve capacitor site IDs in a placement ledger with function/domain/voltage rationale; unused marks are acceptable.

Remove or reroute reviewed shorting copper only after the intended netlist is known. Route Kelvin sense separately from power current; keep gate/switch loops tight and cell inputs away from switching nodes. Define net classes from maximum normal/transient differential voltage, material, pollution/environment and fabrication rules, including copper to holes/edges and isolation boundaries. Calculate charge copper temperature rise and balance dissipation in the enclosed case without a heatsink. Review antenna keepout, USB differential route, CAN return path and accessible test points.

Deliverables: routed matching board, layer/3D review, fixed-geometry comparison, mechanical case overlay, DRC/clearance rationale. Pass: no electrical short/crossing/clearance errors, no unrouted required nets, no unexplained parity issues; all waivers reviewed individually. Repeat checks with final zone fill on a controlled saved revision.

### WP6 — Release and assemble

Dependencies: WP5. Independently review schematic/PCB against TI requirements and complete firmware chain. Produce BOM with exact MPNs and alternates, assembly drawings with polarity, centroid files, Gerbers/drills, stackup, fabrication notes, paste/stencil and programming instructions from one tagged revision. Re-import fabrication outputs and inspect layers/drills, solder-mask bridges, courtyard/case conflicts and connector mating. Check fuse DC interrupt rating against pack voltage and available fault current. Inspect incoming parts and measure shunts before assembly.

Pass: reproducible outputs, manufacturer capability checks satisfied, no generic safety-critical identities and no unreviewed DRC exclusions. Dashboard score and clean DRC are supporting evidence only.

### WP7 — Staged bench acceptance

Dependency: assembled WP6 revision and approved test envelope. Use current-limited isolated supplies/cell simulator first, with logging and a controlled disconnect. Record board/software/package hashes, settings, instrument IDs, measured values and failures. Establish numerical accuracy and response-time budgets before executing tests; the provisional targets below require confirmation against chosen parts and product needs.

1. Unpowered: inspect polarity, shorts, isolation and shunt continuity. Pass: no unintended domain connection; fixed geometry matches baseline.
2. Supplies: power each intended domain at minimum/nominal/maximum inputs, including USB/CAN-only states. Pass: rails remain within all component limits, no backfeed or excessive heat, switches remain off throughout resets.
3. BQs: observe COM gating, address reassignment and both local supplies over repeated cold/warm starts. Pass: lower 0x10 and upper 0x08 uniquely readable, no collisions or overvoltage, successful restart after each single-domain power loss.
4. Cells: sweep every one of 32 simulated channels at low/mid/high voltage, including CELL16 boundary; test open-wire, swapped harness detection and attach sequence under controlled energy. Provisional pass: ≤10 mV error per channel after calibration, correct ordering and fault inhibits charging; refine from TI accuracy and error budget.
5. Temperatures: use precision resistors and controlled thermal points for every enabled cell/MOS channel, then open/short each. Provisional pass: ≤2 °C over operating range and no fault interpreted as a safe temperature.
6. Current/voltage: inject zero and multiple known charging currents, verify polarity, gain and integration; sweep charge/output voltage ADCs. Provisional pass: ≤2% current error above defined minimum measurable current, documented zero offset and ≤1% voltage error, with cutoff margins wider than total error.
7. Charge switch: test enable/disable, charger attach/remove, reverse/off-state leakage and current limit first at low energy. Exercise each voltage, temperature, current and allow-flag threshold plus hysteresis and fault reset. Pass: measured hardware off within the approved response time, no body-diode bypass, no unsafe re-enable and no gate-rating excursions.
8. Balance: command each channel, verify bleed current, mapping and adjacent-cell exclusion including stack boundary. Run worst permitted simultaneous balancing in the closed case. Pass: all resistor/BQ/PCB temperatures below derated limits and measurement disturbance within budget.
9. Failures: disconnect each BQ bus, stall SDA/SCL, stop Lisp, reset ESP32 and remove each supply while charging. Pass: bounded charge-off with no stale-data re-enable; recovery requires fresh valid measurements. Verify CAN/USB reporting and error states.
10. Sleep/wake: button, charger, periodic timer and both BQ wake paths; repeat with lowest allowed cell voltages. Pass: both monitors recover, no boot-strap lockout, switches default off and measured sleep current meets the established pack-storage budget.
11. Advance to rated-voltage/current tests only after the preceding gates pass. Validate load steps, transients, switch SOA and enclosed thermal soak. Repeat the protection tests at the final electrical envelope. Release only with signed evidence and resolved failures.

## Decisions and information still required

Investigation has established concrete faults, but manufacturer pinout checks, visual harness/dashboard comparison and complete component identification are not finished. These are engineering work, not questions for the user. Search local photographs, source, supplied BOM/reference boards and primary manufacturer documents before declaring a part unknowable.

Product inputs genuinely needed before ratings and acceptance limits can be finalized: exact cell chemistry and permitted maximum voltage; intended charger maximum voltage/current and credible transients; required balance current/time; enclosure ambient/ventilation and allowable temperatures; required storage duration/sleep-current budget; and whether the existing harness is already built to an independently verified drawing. Source defaults (4.16/4.21 V charge thresholds, 16 A maximum charge, etc.) are compatibility evidence, not approval of those settings for this pack. No answers are needed to execute WP1 or continue the component investigation.

This plan records completed checks and unfinished investigation separately. Completion of the plan does not certify the present hardware or firmware for use.

## User-confirmed product inputs — November 3, 2026

- Cells: RS50 (corrected by the user November 4, 2026). Verify the exact manufacturer and cell datasheet before final voltage settings and ratings.
- Charger: 5 A. This establishes nominal charger current; the supplied 16 A software default is not automatically the selected charge-overcurrent threshold. Charger output voltage/tolerance remains to be established.
- Temperature limits: use the supplied firmware/package reference definitions as the intended baseline, including charge cell range 0–45 °C, charge MOS limit 85 °C and balancing cell/IC maxima 45/85 °C. Verify runtime settings and actual sensor fault handling against these definitions.
- Harness: supplied folder photographs and wiring reference are the evidence to inspect; do not ask the user to recreate the mapping. The wiring image was visually opened in this session. It depicts 32s cell wiring, four external temperatures, CAN and enable override, but does not by itself prove the current PCB connector pad numbering.

These inputs supersede the corresponding requests above for cell identity, nominal charging current, source of temperature limits and harness-reference location. Continue the remaining pin-level and photographic investigation before asking for additional mappings.

### Pack and charger clarification

User confirmed 32S1P RS50 pack and a 134 V, 5 A charger. These are the selected nominal product inputs; pack configuration and nominal charger voltage are no longer open questions. Charger nominal power is 670 W and nominal average cell voltage at 134 V is 4.1875 V. Actual charger tolerance, transients and individual-cell imbalance remain engineering verification items; the pack-average voltage does not replace per-cell cutoff checks.

## WP1 execution checkpoint and implementation priority — November 3, 2026

See [durable WP1 evidence](docs/wp1-2026-11-03/README.md). Fresh collection records 150 footprints, 655 physical pad instances and 45 fixed connector/R_B footprints. Pad assignment/position/rotation comparison against the prior inventory has zero differences. Regenerated DRC reports 650 violations (199 shorts, 60 crossings), 146 unconnected items and 366 parity issues; ERC reports 121. SHA-256 baseline, fixed geometry, full pad ledger, object-level short/crossing classification and regenerated reports are retained under docs/wp1-2026-11-03/.

WP1 is **partially executed, not passed**: independent harness mating/polarity confirmation, complete manufacturer identity/pinout/rating review and complete visual checks remain open. Do not describe automated classification as individual electrical disposition or assigned pad nets as verified continuity.

The next implementation package is **reference-based schematic construction, starting with the two 16-cell BQ sheets**, followed by isolated/gated upper communications and wake, then ESP32/power/sensing/charge-only control. These sheets can be drafted incrementally while unresolved component choices are explicitly marked; full procurement and bench closure need not precede schematic progress. Preserve fixed board geometry and defer PCB netlist import until schematic review. This investigation did not authorize or perform schematic, PCB or firmware edits.

Source corrections: the supplied header selects PCB_VERSION=2; BQ7695202 defaults to CRC-enabled I2C and enabled 3.3 V REG1 according to TI's device table. Startup supply/wake analysis must use that exact variant. Lisp has crash/re-init handling, but charge-off follows init-hw, so a bounded fail-off response remains unproven. See the checkpoint for the exact distinction between verified source behavior and required adaptation.

## Separate BQ monitor repair and disconnect — November 3, 2026

The separate `qfbms32-bq-monitors` project has five corrected lower temperature series paths, an ISO1640 8-D barrier and a selected TI TMUX154EDGSR two-line disconnect. Fresh XML checks its actual signal/control pins and preserves lower/upper returns and the temperature regression checks. A maintained, separate C/Lisp adaptation enforces address 0x10 verification before upper admission and gates repeated Lisp requests. Reproducibility and focused source/model checks pass. KiCad 10 ERC is zero errors / 42 warnings (30 isolated cell-tap labels, eight pin-type reports and four embedded-library warnings); two pending-stub endpoint warnings from the prior 43-warning report are gone and the custom switch adds one library-table warning. Full evidence and OPEN electrical checks are in [the disconnect implementation note](docs/bq-disconnect-2026-11-03.md), with the preceding changes in [the repair note](docs/bq-repair-2026-11-03.md).

The package stopped before ESP32 circuitry, host power, charge switching, USB, CAN, PCB reconciliation or bench validation. Next concrete work is to establish the HOST_3V3/lower-REG1 voltage and power-sequencing envelope, size both I2C pull-up pairs for current and rise time with the ISO1640 side-1 80 pF limit, and verify the lower-BQ partial-power behavior. Existing shunt topology, Kelvin pickup and calibration remain provisional. No PCB import is authorized.
