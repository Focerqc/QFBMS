# BQ monitor schematic increment — November 3, 2026

Charge-only schematic increment for the two BQ7695202 monitors. Discharge protection is out of scope. There is no heatsink. Current status is recorded in the [repair note](bq-repair-2026-11-03.md), which supersedes this original increment. The upper-I2C isolation sheet is documented in [bq-iso-i2c-2026-11-03.md](bq-iso-i2c-2026-11-03.md). GPIO9 must be pulled high at reset on that sheet, because GPIO9 low selects ESP32-C3 download mode.

`qfbms32.kicad_pcb`, `qfbms32.kicad_sch`, and `qfbms32.kicad_pro` were not modified. No netlist was imported, no historical generator was run, and no zones were refilled. `qfbms32-charge-only-draft.kicad_sch` was not imported. Its heatsink sentence and H2440 note have no authority.

## Files

Open `qfbms32-bq-monitors.kicad_pro`. It is a separate project from the working board.

- `qfbms32-bq-monitors.kicad_sch` — root sheet with the two monitor sheets.
- `qfbms32-bq-lower.kicad_sch` — lower monitor, `U_BQ1`.
- `qfbms32-bq-upper.kicad_sch` — upper monitor, `U_BQ2`.

Symbols, wires, labels, and power symbols are real KiCad objects. The BQ symbol is the KiCad `BQ76952PFB` symbol renamed for the BQ7695202, with pins 19 and 44 shown and pin 49 added for the exposed pad on the working-board footprint `Package_QFP:TQFP-48-1EP_7x7mm_P0.5mm_EP5x5mm_ThermalVias`. SLUSE13B package outline PFB0048A is a TQFP with no exposed thermal pad. Pin 49 is tied to the local reference so that footprint copper is not left floating. It is not a claim that the TI silicon has a bonded thermal pad.

## Lower monitor, U_BQ1

Local reference and exposed pad are `CELL0`. Cells are `CELL1` through `CELL16`, so VC0 is `CELL0` and VC16 is `CELL16`.

Cell inputs copy the TI filter from SLUSE13B section 7.3 and EVM user's guide SLUUC33A section 5.4 Figure 5-9: 20 Ω in series with each of VC0–VC16, 220 nF between adjacent filtered nodes, and 220 nF from the VC0 node to local VSS. Section 7.3 allows 20–100 Ω and 0.1–1 µF. The VC pins are also the internal balance pins (Table 6-1). Host balancing is the firmware mode. The external balance network is not drawn. R_B1–R_B33 stay fixed for the case and are not on this sheet. Those 33 resistors are not a 33-cell stack.

BQ7695202 is CRC I2C, and REG1 defaults to enabled at 3.3 V (SLUSE13B section 5). That default does not replace the REG0 preregulator or the wake pins. REG18 uses 2.2 µF, inside the 1.8–22 µF range in section 7.10. REG1 uses 1 µF (section 7.12). REGIN uses 22 nF (section 7.11; allowed 15–27 nF). The 150 pF BREG figure in section 7.11 is the table maximum, not a fitted capacitor. The BAT pin uses the Figure 16-2 series 100 Ω, 1 µF, and 100 pF, through its own diode. The REG0 collector diode is a second diode, as section 16.2 requires. CP1 is tied to BAT because the charge pump is unused (Table 16-3). Enabling the charge pump with that connection adds about 200 µA.

SRP and SRN are one Kelvin pair for the charge shunt. The filter is 100 Ω and 100 nF at the device (sections 16.2 and 18.1). The optional 100 pF and 0.1 µF-to-VSS capacitors in those sections are not fitted. SRP is the `CELL0` end and SRN is the `CHG-` end, so charging current makes SRP positive relative to SRN (pin descriptions in section 6). The separate schematic provisionally draws one shunt. Existing working-board shunt topology, Kelvin pickup and combined C/Lisp calibration remain provisional. This drawing does not authorize a board topology change or establish a purchased resistance. `CHG-` is a sheet port.

I2C is the host bus at 100 kHz: SDA is ESP32 GPIO21 and SCL is GPIO20. Startup 7-bit address is 0x08. Firmware then moves this device to 0x10. Pull-ups are on this domain's REG1.

TS1, TS3, ALERT, DCHG, and HDQ are the firmware temperature inputs. The firmware uses the internal 18 kΩ pull-up and assumes a 10 kΩ, beta-3380 NTC with a 500 Ω subtraction from inferred resistance. R27–R31 now connect in series to RT1–RT5 after the repair. Fitted resistance and sensor MPN remain OPEN; the subtraction is a compatibility assumption, not a verified part value. No EVM external thermistor-bias resistor is fitted. The optional thermistor capacitor under 4 nF (section 16.2) is not fitted.

RST_SHUT has a pulldown to local VSS because section 12.6 requires the pin low in normal operation. TS2 is the shutdown wake pin and has no thermistor (section 13.5). LD is the other wake input from SSZT191. The upstream driver for RST_SHUT, TS2, and LD is a sheet port. LD must stay inside the section 7.3 voltage range versus this domain's VSS.

CHG, DSG, PCHG, and PDSG are left floating (Table 16-3). Discharge protection is out of scope, and the charge FET is not on this sheet. FUSE and REG2 are left floating (Table 16-3). Pins 19 and 44 are not connected to silicon. CFETOFF, DFETOFF, and DDSG are tied to local VSS. PACK uses 10 kΩ to `CELL16`, the no-high-side-FET connection in section 16.2.

## Upper monitor, U_BQ2

Local reference and exposed pad are `CELL16`, not the lower ground. Cells are `CELL17` through `CELL32`, so VC0 is `CELL16` and VC16 is `CELL32`. The cell filters, local decoupling, regulator pins, and wake pins repeat in this domain. No net on this sheet joins the lower ground, lower SRP, or lower SRN. The only shared pack node is `CELL16`, which is the lower top cell and the upper reference.

Unused current inputs are terminated as TI specifies for unused current measurement. SLUSE13B section 16.6, Table 16-3, pins 18 and 20 (SRP, SRN):

> If not used, these pins should be connected to pin 17 (VSS).

Upper VSS is `CELL16`, so upper SRP and SRN connect to `CELL16`.

SDA, SCL, and ALERT leave this sheet for the isolation sheet. ISO1640 is drawn there, but GPIO9 only reaches R203; the host-side disconnect is PENDING with both paths separated. Local SDA and SCL pull-ups are on this domain's REG1. The upper 7-bit address is 0x08, and only after the lower device has been verified at 0x10. That gating remains PENDING and is not implemented.

Upper TS1, TS3, HDQ, DCHG, CFETOFF, DFETOFF, and DDSG are tied to upper VSS. The firmware temperature map does not consume those upper pins. TS2 remains the wake pin and is not tied to VSS.

## Connector notes

These are assigned PCB nets, not harness proof. The connector value labels are wrong. No physical connector is relabeled from the wiring photo.

- J_CELL1 pins 1–10 are CELL9 down to CELL0.
- J_CELL2 pins 1–9 are CELL18 down to CELL10.
- J_CELL3 pins 1–8 are CELL26 down to CELL19.
- J_CELL4 pins 1–6 are CELL32 down to CELL27.

## ERC

KiCad 10.0.6:

```text
kicad-cli sch erc --severity-all --format json --output exports/bq-monitors-erc.json qfbms32-bq-monitors.kicad_sch
```

Historical two-sheet result: 40 violations, 0 errors, 40 warnings. Current repair result: zero errors and 43 warnings; see the [repair note](bq-repair-2026-11-03.md).

| Sheet | Warnings |
| --- | ---: |
| Root | 32 |
| Lower monitor | 3 |
| Upper monitor | 5 |

Warning classes:

- 30 `isolated_pin_label`. `CELL1`–`CELL15` and `CELL17`–`CELL31` each connect to one filter resistor. The harness is not part of this increment, so each of those labels has a single pin. `CELL0`, `CELL16`, and `CELL32` are the reference and stack-top nets and are not in this class.
- 8 `pin_to_pin`. CFETOFF, DFETOFF, DDSG, and on the upper sheet also HDQ and DCHG, are tied to the local reference. The power flag that drives that reference is a power output, so ERC reports a bidirectional pin on a power-output net. The tie is the Table 16-3 unused-pin termination.
- 2 `lib_symbol_issues`. The modified BQ7695202 symbol is embedded as `qfbms:BQ7695202PFB`. The project symbol library table has no `qfbms` entry. The symbol is stored in the sheet.

Ignored ERC checks in this KiCad configuration, not run as failures: single global label, four-way junction, SPICE model issue, and footprint-filter mismatch.

## OPEN items

A value is OPEN when the datasheet or the firmware interface does not fix it. No MPN was selected for any part on these sheets. No LTC7138, charge FET, USB, or CAN device is present.

### Lower sheet

| Reference | What is open |
| --- | --- |
| D1 | BAT series diode. MPN, voltage rating, and footprint. Separate from the REG0 collector diode. |
| D2 | REG0 collector diode. MPN, voltage rating, and footprint. |
| Q1 | REG0 NPN. MPN and footprint. It must tolerate this monitor's own stack, not the full 32s pack. |
| R19 | BREG-to-VSS resistor. Section 16.2.2 says a large resistor such as 10 MΩ; the value is not otherwise fixed. |
| R20, R21 | SDA and SCL pull-ups to this domain's REG1. Resistance is open at 100 kHz. |
| R23 | RST_SHUT pulldown. Section 12.6 requires a low pin; it does not fix the resistance. The upstream driver is the sheet port `RST_SHUT_BQ1`. |
| R24 | LD series resistor. Value, MPN, and footprint. The upstream source is `LD_WAKE_BQ1`. |
| R_SH | The one charge shunt. Value, MPN, and footprint. Not the R001 silkscreen value, and not both existing shunt footprints in series. `CHG_NEG` continues on a later sheet. |
| R27, RT1 | TS1 series resistor and NTC. Firmware subtracts 500 Ω and assumes 10 kΩ, beta 3380. |
| R28, RT2 | TS3 series resistor and NTC. Same firmware assumption. |
| R29, RT3 | ALERT series resistor and NTC. Same firmware assumption. |
| R30, RT4 | DCHG series resistor and NTC. Same firmware assumption. |
| R31, RT5 | HDQ series resistor and NTC. Same firmware assumption. |
| R1–R17 | 20 Ω cell-input resistors. Value is the TI filter. Footprint, power rating, and MPN are open. |
| R18 | 100 Ω BAT series resistor from Figure 16-2. Footprint and MPN are open. |
| R22 | 10 kΩ PACK resistor from section 16.2. Footprint and MPN are open. |
| C1–C17 | 220 nF cell-input capacitors. Footprint is `C_0603_1608Metric`. Voltage rating and MPN are open. |
| C18, C19 | BAT 1 µF and 100 pF. Footprint and MPN are open because these sit on the local stack. |
| C20 | 22 nF REGIN. Footprint is 0603. MPN is open. |
| C21 | 2.2 µF REG18. Footprint is 0603. MPN is open. |
| C22 | 1 µF REG1. Footprint is 0603. MPN is open. |
| C23 | 100 nF SRP–SRN filter. Footprint is 0603. MPN is open. |
| R25, R26 | 100 Ω SRP and SRN resistors. Footprint is 0603. MPN is open. |
| — | External balance network, including the role of fixed R_B1–R_B33. |
| — | Upstream wake sources on `TS2_WAKE_BQ1`, `RST_SHUT_BQ1`, and `LD_WAKE_BQ1`. |

### Upper sheet

| Reference | What is open |
| --- | --- |
| D101 | BAT series diode. MPN, voltage rating, and footprint. |
| D102 | REG0 collector diode. MPN, voltage rating, and footprint. |
| Q101 | REG0 NPN. MPN and footprint. |
| R119 | BREG-to-VSS resistor. Same 10 MΩ example as the lower sheet; value is open. |
| R120, R121 | SDA and SCL pull-ups to upper REG1. Resistance is open. |
| R123 | RST_SHUT pulldown. Value is open. Upstream port is `RST_SHUT_BQ2`. |
| R124 | LD series resistor. Value, MPN, and footprint. Upstream port is `LD_WAKE_BQ2`. |
| R101–R117 | 20 Ω cell-input resistors. Footprint, power rating, and MPN are open. |
| R118 | 100 Ω BAT series resistor. Footprint and MPN are open. |
| R122 | 10 kΩ PACK resistor. Footprint and MPN are open. |
| C101–C117 | 220 nF cell-input capacitors. 0603 footprint; voltage rating and MPN are open. |
| C118, C119 | BAT 1 µF and 100 pF. Footprint and MPN are open. |
| C120–C122 | 22 nF REGIN, 2.2 µF REG18, and 1 µF REG1. 0603 footprints; MPNs are open. |
| — | External balance network. |
| — | Upstream wake sources. `SDA_BQ2`, `SCL_BQ2`, `ALERT_BQ2`, and `REG1_BQ2` continue on the isolation sheet; see [bq-iso-i2c-2026-11-03.md](bq-iso-i2c-2026-11-03.md). |

### Root sheet ports left for later sheets

`CHG_NEG`, `RST_SHUT_BQ1`, `TS2_WAKE_BQ1`, `LD_WAKE_BQ1`, `RST_SHUT_BQ2`, `TS2_WAKE_BQ2`, `LD_WAKE_BQ2`, `GPIO9`, and `HOST_3V3` remain open on the root where the peer sheet does not exist yet. `SDA_HOST`, `SCL_HOST`, `SDA_BQ2`, `SCL_BQ2`, `ALERT_BQ2`, and `REG1_BQ2` are wired to the isolation sheet. They are open interfaces or isolation-sheet nets, not unused silicon pins.
