# Upper BQ bus disconnect — November 3, 2026

This package extends the separate `qfbms32-bq-monitors` schematic and adds a maintained firmware adaptation. It reuses the frozen evidence under [`wp1-2026-11-03`](wp1-2026-11-03/); it did not repeat board investigation. Grok commits `78c5ac6` and `c8f5122` remain intact. The working `qfbms32.kicad_pcb`, `qfbms32.kicad_sch`, `qfbms32.kicad_pro`, and `_reference/firmware/` baseline remain untouched. No PCB netlist import or zone refill was performed.

## Selected device and verified pin map

The host-side two-line disconnect is TI **TMUX154EDGSR**, DGS 10-pin VSSOP, symbol `U204`, footprint `Package_SO:TSSOP-10_3x3mm_P0.5mm`. The TI datasheet gives VCC 3.0–4.3 V, powered I/O range 0–VCC, powered-off high-impedance I/O with VCC = 0 V, and I/O tolerance up to 5.25 V in the powered-off condition. The two bidirectional channels have 10 Ω maximum on resistance and 7.5 pF typical on capacitance. The product is active and TI lists I2C among supported protocols. Source: [TMUX154E datasheet, SCDS379](https://www.ti.com/lit/ds/symlink/tmux154e.pdf), especially sections 5–8 and the package addendum.

| DGS pin | TI signal | QFBMS connection |
| --- | --- | --- |
| 1 | SEL | CELL0; selects channel port 0 |
| 2 | A0 | ISO1640 side-1 SDA, `SDA_ISO_SIDE` |
| 3 | A1 | No connect |
| 4 | A | Lower/host SDA, `SDA_HOST` |
| 5 | GND | CELL0 |
| 6 | B | Lower/host SCL, `SCL_HOST` |
| 7 | B1 | No connect |
| 8 | B0 | ISO1640 side-1 SCL, `SCL_ISO_SIDE` |
| 9 | EN | GPIO9 directly |
| 10 | VCC | HOST_3V3 |

TI's function table says EN low enables and EN high disables; SEL low routes A/B to A0/B0. Therefore GPIO9 low connects both lines and GPIO9 high opens both. R203 already pulls GPIO9 up at reset, preserving the ESP32-C3 boot requirement. Unlike the rejected TCA9517A candidate, this switch passes the ISO1640's intentional side-1 low offset without a buffered-low threshold. Its actual control and signal pins are checked from fresh KiCad XML.

The TMUX154E powered supply must remain in 3.0–4.3 V, and powered signal levels must remain between 0 V and VCC. HOST_3V3 is the selected schematic supply, but its implementation and tolerance are later work. Confirm the maximum of HOST_3V3, lower REG1 and all bus pull-up levels stays within the selected part's operating/absolute limits. With VCC off, the datasheet specifies high-impedance I/O and up to 5.25 V on its I/O pins; this addresses powered-off backfeed across this switch, not back-power into the lower BQ from the still-connected ESP32/lower bus.

## Pull-ups, loading and remaining electrical checks

The lower-side pull-ups R20/R21 remain on lower REG1. R201/R202 pull up the switch/ISO1640 side-1 segment to HOST_3V3. When U204 closes, both pull-up pairs share the same SDA/SCL nets. Values remain OPEN because the host supply, lower REG1 tolerances, pull-up sink-current requirements, and bus capacitances are not yet fixed. Calculate cross-rail current while connected, combined low-state current at the BQ/ESP32/ISO1640, and rise time with every attached device and probe load before assigning values.

The ISO1640 side-1 limit remains 80 pF, including the selected switch, wiring, pull-ups, and device pins. The switch contributes 7.5 pF typical when on; use the datasheet's guaranteed limit when available and leave margin. The ISO1640 datasheet states side-1 output low is as high as 710 mV and side-1 sink capability is 3.5 mA; this direct pass switch does not impose a separate 0.45 V buffer threshold. Its orderable suffix remains OPEN, and the existing 8-D pinout remains unchanged. Do not substitute the 16-DW pin map.

Other unresolved power cases: firmware baseline enables ESP32 internal I2C pull-ups on GPIO20/21; these are on the lower bus and can back-power the lower BQ if host power is present while the lower REG1/device is off. The host-power implementation, lower REG1 versus HOST_3V3 startup order, aggregate sink current, pull-up values, bus capacitance/rise time, and bench communication remain OPEN. This schematic selection does not claim those cases are resolved.

## Firmware admission behavior

The maintained adaptation is in [`firmware/qfbms32-adaptation`](../firmware/qfbms32-adaptation/README.md). `_reference/firmware/` remains the compatibility baseline. The adaptation checks the lower address-register write, config exit and communication-mode commands, then requires a successful `Cell2Voltage` read at `0x10` (up to three attempts) before it drives GPIO9 low. Failed setup or failed reads leave GPIO9 high, keep address `0x08` blocked, and return initialization failure. Recovery after uncertain address state requires a later initialization retry or explicit BQ recovery/power cycle; there is no automatic speculative access to `0x08`.

Every Lisp GPIO9 write now calls the guarded `bms-set-com` extension, including `with-com`, forced communication and CAN-related paths. The C helper rejects connection requests before lower `0x10` verification and rejects 0x08 BQ transactions while the path is open, except during the explicit lower address-change phase. Gate changes serialize with I2C and occur only while both GPIO lines read high; a busy/stuck-low bus leaves the current gate state and reports denial. Three lower-address read attempts are the defined retry policy. The code has not been built against VESC Express or bench-tested in this package.

## Verification

From the repository root:

```powershell
python _tools/gen_bq_monitor_sheets.py
python _tools/check_bq_reproducibility.py
kicad-cli sch erc --severity-all --format json --output exports/qfbms32-disconnect-erc.json qfbms32-bq-monitors.kicad_sch
kicad-cli sch export netlist --format kicadxml --output exports/qfbms32-disconnect.xml qfbms32-bq-monitors.kicad_sch
python _tools/verify_bq_repair.py exports/qfbms32-disconnect.xml
python _tools/check_bq_bus_admission.py
kicad-cli sch export svg --output exports/qfbms32-disconnect-svg qfbms32-bq-monitors.kicad_sch
```

The reproducibility checker passed clean-input generation and a byte-identical second generation. The fresh XML pin checker passed the five repaired temperature chains, both actual TMUX signal channels, SEL, GPIO9 control, supply and ground, upper/lower isolation supplies, upper returns, ALERT isolation, and lower sense separation. The focused firmware source/model checks passed address-write failure, failed/retried 0x10 verification, successful admission and repeated Lisp gate requests.

KiCad ERC reports **42 warnings and zero errors**: 30 `isolated_pin_label` reports on cell-tap labels, eight intended `pin_to_pin` type reports, and four `lib_symbol_issues` because the local `qfbms` embedded symbols are not in the machine's configured library table. Relative to the 43-warning repair report, the two pending-stub endpoint warnings are gone and the custom switch adds one library-table warning. No ERC check was suppressed. The inherited ignored checks remain single-global-label, four-way-junction, SPICE-model and footprint-filter diagnostics. KiCad CLI again logged denied sandbox registry access and the generic schematic annotation warning; exports completed, as with the prior repair.

The SVGs and a four-page PDF were generated for the root, lower, upper and isolation sheets and visually inspected. The isolation sheet shows U204's paired channels, reset-high control, separate-domain ISO1640 rails and local bypass. The local open pull-up/rail checks above are not ERC-detectable and remain explicit review items.

## Protected files and stop point

Hashes before and after this package are recorded in `exports/qfbms32-disconnect-hashes.json`. The three working design files must remain equal to the known WP1 hashes. The separate firmware adaptation hashes are also recorded there to show that the supplied baseline stayed unchanged.

This package stops after the disconnect and firmware admission work. It does not implement ESP32 circuitry, host power, charge switching, USB, CAN, PCB reconciliation, fitted sensor values, or bench verification. The next work should resolve the HOST_3V3/lower REG1 envelope and I2C pull-up/load budget before treating this path as electrically closed.
