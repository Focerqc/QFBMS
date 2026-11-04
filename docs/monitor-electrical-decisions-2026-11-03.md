# Monitor electrical decisions — November 3, 2026

Documentation-only checkpoint. No schematic, PCB, generator or firmware edits are part of this checkpoint. This supplements the disconnect implementation note; it does not close its OPEN electrical checks or authorize PCB import.

## Architecture requirements

- Preserve the ISO1640 barrier between CELL0 and CELL16 domains. U204 TMUX154E disconnects the host-side path to ISO1640 side 1; it does not join the upper electrical bus to host ground. GPIO9 high opens U204; low connects it after lower address 0x10 verification. Upper address remains 0x08.
- Budget ISO1640 side-1 loading per SDA/SCL line with U204 both open and closed. Maximum is 80 pF, including connected lower BQ, ESP32, switch, isolator, traces, pads, protection and probe loading. Short routing alone does not prove compliance. Use 60 pF as a provisional design budget, leaving 20 pF below the published maximum; verify actual component maxima and routed loading before closure.
- HOST_3V3 powers the host and ISO1640 side 1. Upper REG1 powers side 2 relative to CELL16. Lower REG1 remains a separate rail until their tolerance and sequencing relationship is established. Do not assume the lower BQ starts first.
- Upper unused SRP pin 18 and SRN pin 20 connect to upper VSS pin 17 / CELL16 per TI Table 16-3. The separate draft already implements this; the main PCB needs reconciliation. Do not connect either upper sense pin to the lower shunt.
- Each monitor needs a controlled wake path that operates without its REG1 rail. TS2 must be pulled toward that monitor's own VSS for wake and released afterward. A permanent TS2-to-VSS tie can prevent SHUTDOWN and is not selected. Upper actuation must cross domains through a rated interface or use a local contact; its driver, leakage and timing remain OPEN.

## Pull-up candidate calculations

Firmware baseline is 100 kHz. Evaluate 4.7 kOhm, 1% for R20/R21 and R201/R202 as the preferred candidate, not a fitted-value decision. Keep upper R120/R121 subject to a separate side-2 calculation. Both host-domain pull-up pairs remain connected to different rails in the present draft.

For an illustrative bound where BOTH pull-up rails are at most 3.6 V, external pull-up current at VOL = 0 is bounded by sum(Vrail_max / Rmin). With two equal resistors per line:

- 4.7 kOhm: Rmin = 4653 Ohm; combined current <= 1.547 mA per low line.
- 3.3 kOhm: Rmin = 3267 Ohm; combined current <= 2.204 mA per low line.

These bounds exclude internal pull-ups, other bus loads and transient currents. The 3.6 V host-rail maximum is an assumption, not an established HOST_3V3 specification. Check every possible low-driving device's guaranteed VOL/IOL and every receiver's VIL, including ISO1640's offset low through U204, before acceptance.

First-order rise time is tr = 0.8473 * Rp * C. At 80 pF and maximum 1% resistor tolerance:

- One 4.7 kOhm pull-up: 322 ns; two equal connected pull-ups: approximately 161 ns.
- One 3.3 kOhm pull-up: 226 ns; two equal connected pull-ups: approximately 113 ns.

These are ideal RC estimates for the applicable connected load, not waveform verification. The single 4.7 kOhm / 80 pF case meets the 100 kHz 1000 ns rise-time limit, but not the 400 kHz 300 ns limit. Do not change firmware speed based on the closed-switch result. Include switch resistance and actual capacitance in final analysis.

A 0.6 V difference between two rails coupled through two nominal 4.7 kOhm resistors produces about 64 uA per idle-high line in a simplified unloaded model. This is cross-rail current, not proof of rail compatibility. A disabled regulator may not sink that current safely; analyze intermediate and off states explicitly.

## Partial-power closure criteria

The existing upper disconnect does not disconnect the lower BQ from the ESP32. Firmware high impedance does not remove external pull-ups; series resistors do not provide isolation. Do not select either as the complete back-power mitigation.

Select and verify a lower-interface hardware solution with specified powered-off behavior, or a power architecture that demonstrably prevents drive into an unpowered lower monitor. No specific additional device is selected here. Check HOST on/BQ off, HOST off/BQ on, upper off, brownout, reset and shutdown, including SDA/SCL, ALERT, wake and every other crossing. Bound pin voltage and injection/leakage from manufacturer specifications. Account for enabled ESP32 internal I2C pull-ups. GPIO9 controls U204 and is not itself a lower-BQ connection in this draft.

REG1's nominal 3.3 V setting spans 3.0–3.6 V under TI's stated conditions; verify REGIN headroom, regulator current and preregulator dissipation. REGIN requires a low-voltage source or the BREG-controlled external NPN preregulator, not a direct half-stack connection. SHUTDOWN loses volatile configuration; startup must restore address/configuration before upper admission. Ordinary serial reads do not exit DEEPSLEEP; use its explicit exit command or a specified hardware event.

## Reconciliation gates

### Lower-interface investigation follow-up

Prioritize lower-BQ powered-off isolation before selecting wake GPIOs. Moving the existing upper ISO1640/U204 supplies to lower REG1 does not remove the direct ESP32-to-lower-BQ SDA/SCL path. Switching only external pull-ups also leaves ESP32 internal pulls and any active signal drivers to address.

A dedicated second ISO1640B interface is a concrete candidate for the lower branch: side 1 VCC = HOST_3V3, side 2 VCC = REG1_BQ1; both ground pins = CELL0. Move lower BQ SDA/SCL and R20/R21 onto side 2, with those pull-ups only on REG1_BQ1. Keep the upper branch behind its existing GPIO9-controlled U204 and ISO1640. This uses the isolation barrier for supply separation even though the two lower-interface grounds share a reference. It is a candidate, not a released component/topology selection.

TI section 8.6 Table 8-2 specifies I2C outputs high impedance when VCC1 < 2.3 V or VCC2 < 1.7 V. Section 8.4.1 describes side-2 hot-swap behavior during power-up. Thus a host-side high cannot directly source the lower BQ bus through this barrier. Still verify ramp-region behavior, both-off state, discharge of REG1 and all non-I2C connections; do not generalize that table to GPIO outputs or all brownout voltages.

This topology invalidates the earlier shared-REG1/HOST pull-up model: R20/R21 would no longer parallel the host pulls. Recalculate each branch and host pull-up count, offset-low compatibility among the two host-side isolator ports, connected capacitance and timing before selection. Both host-side 80 pF limits apply to their connected load. Do not simply add another pair of pull-ups. The host nominal 3.3 V rail also needs a guaranteed minimum above the side-1 operating minimum with ripple margin.

The lower REG1 load budget must include the new isolator's worst-case side-2 supply current plus both low-line pull-up currents and every existing load. At 3.6 V and 4.7 kOhm 1%, the two local pull-ups together contribute up to 1.547 mA when SDA and SCL are both low. Add device supply current separately. This is not a completed 45 mA regulator or preregulator thermal budget.

For wake, prefer evaluating a phototransistor optocoupler output directly between TS2 (collector) and the respective local VSS (emitter); an LED driven from HOST power needs no monitor-side REG1 supply. A local output transistor does not need to withstand the full pack voltage across collector/emitter: that voltage is TS2-to-local-VSS, while the optical barrier must withstand the cross-domain voltage and transients. Exact optocoupler MPN, guaranteed hot off-leakage, CTR at selected LED current, saturated VOL, pulse timing, LED driver and available host GPIO remain OPEN. A supply-powered digital isolator cannot operate its output with REG1 absent without an independent upper supply. No spare GPIO assignment has been assumed.

Supply closure also requires the selected REG0/BREG external transistor and REGIN bypass network, minimum headroom and maximum dissipation. Cell balancing is not automatically a REG1 output load: budget actual REG1 consumers and evaluate balancing-induced supply disturbance separately. No assertion of complete electrical closure is made by this follow-up.

1. Close host supply range, lower partial-power hardware, controlled wake, exact part suffixes, pull-up and capacitance budgets.
2. In a separate hardware-change package, implement those decisions in the monitor draft and export a fresh netlist/ERC report. Check actual pins and domains, not labels alone.
3. Prepare a pin-level main-schematic reconciliation and reviewable netlist diff, including displaced symbol coordinates and obsolete charge/discharge labels.
4. Obtain the requested schematic-diff approval before PCB net updates. Apply reviewed changes to a saved board copy first; compare connector and R_B1–R_B33 UUID, XY, orientation, side and pad geometry against the frozen baseline.

Electrical checks remain OPEN until their quantitative and hardware evidence exists. This note does not claim the current circuit prevents back-power or wakes both monitors.

## Sources

- [TI ISO164x datasheet SLLSFC2D](https://www.ti.com/lit/ds/symlink/iso1640.pdf): side-1 80 pF and 3.5 mA limits, side-2 400 pF limit and electrical tables.
- [TI BQ76952 datasheet SLUSE13B](https://www.ti.com/lit/ds/symlink/bq76952.pdf): sections 7.12, 12.3, 13.4–13.5 and Table 16-3.
- [TI stacked-monitor guidance SSZT191](https://www.ti.com/lit/pdf/sszt191).
- Repository evidence: `docs/bq-disconnect-2026-11-03.md`, `docs/FIRMWARE_INTERFACE.md`, and `_tools/gen_bq_monitor_sheets.py` (read only; not executed).
