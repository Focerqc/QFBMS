> Historical snapshot from before the 2026-11-02 repository split.
> May contain conflicting or unverified electrical instructions; not current editing guidance.
>
> Superseded by the [current build plan](../../PLAN.md) and [design rules](../../DESIGN_RULES.md).
> This remains a dated inventory. Its inferred part functions, placement restrictions, and electrical proposals are not the current specification.

# Placed parts on qfbms32

Inventory of the 150 footprints on `qfbms32.kicad_pcb`, read from that file on 27 Oct 2026. Nothing here was moved, renamed, rerouted, or given a new value.

Sources, in the order that wins: the footprint that is already placed, its value field, and its pad nets; the photos in `_reference/user_photos/` (IMG_2143–IMG_2150); then the TI BQ76952 pin functions and the usual EVM values. The VBMS32 firmware under `_reference/firmware/` is the charge-only board these photos are of. It names GPIOs and divider ratios. It is not a schematic of this file.

Coordinates are millimetres in the KiCad file. Small Y is the edge with the buck, the relay, and the buzzer. Large Y is the cell-connector edge. Small X is the XT30 end. Large X is the USB end.

**known** — the nets, the value, and the position agree, or the part is the chip or connector printed on the board.
**probable** — position and value fit a job, and the pads are still empty or the reference is an old name.
**unknown** — no job assigned.

Markings stored as a code: `1000` is the 4-digit code for 100 Ω. `2203` is 220 kΩ. `474` is 470 kΩ. `01X` is the EIA-96 mark for 10.0 Ω. `R001` is 1 mΩ. `107C` on the yellow tantalum in IMG_2146 is 100 µF, 16 V, which matches `C_TAN1`.

Copper, from the board's connectivity: 41 footprints touch a neighbor. That is the four cell jacks, the 32 `R_F` resistors (cell side only), `J_BAT1` pad 1 to `F1`, and `C_SSR1` / `C_SSR2` to `U_SSR1` on `VBOOST` and `GND`. The other 109 footprints are islands. `CELL0` is the tap with no filter resistor.

## TI jobs that still need a placed part

These are the usual BQ76952 parts. The footprints that could be them are called out. Where none fits, the pin is named.

| Job | Usual part | What is actually placed |
|---|---|---|
| VC0 series 20 Ω | 20 Ω into pin 16 | `R_F1`–`R_F32` already take `CELL32` down to `CELL1`. No 20 Ω is left for pin 16. `U_BQ1` pin 16 (`VC0`) is net `CELL0`. `U_BQ2` pin 16 (`VC0`) is net `CELL16`. |
| BAT filter | series resistor into pin 47, cap to VSS | `U_BQ1` pins 47 (`BAT`) and 48 (`VC16`) are both net `BQ1_VC16`. `U_BQ2` pins 47 and 48 are both net `BQ2_VC16`. No resistor sits between those two pins. |
| REG18 / REG1 / REG2 / REGIN caps | about 1 µF to 2.2 µF on pins 24, 35, 34, 36 | Those pins have no net. No capacitor footprint sits on them. `C_F*` are the 0.22 µF cell caps on the back. |
| CP1 charge-pump cap | cap from pin 46 to BAT | Pin 46 has no net and no capacitor. |
| SRP / SRN filter | 100 Ω each, then about 0.1 µF | **`R_S1` and `R_S2` are the likely series resistors.** See below. The only 100 nF on the board is `C_SSR1`, and its pads are `VBOOST` and `GND`. |
| Thermistor bias | EVM uses 10 kΩ to REG18 | The only footprint stored as 10 kΩ is `R_SSR2`, and its pads are `Q1_GATE` and `GND`. The VBMS firmware turns on the BQ's own 18 kΩ thermistor pull-up instead (`TS1`, `TS3`, `ALERT`, `DCHG`, `HDQ` set as ADC inputs with that pull-up). |
| I2C pull-up | 10 kΩ on SCL and SDA | No free 10 kΩ is placed. Both monitors' pin 26 (`SCL`) and pin 27 (`SDA`) have no net. Firmware `PIN_SCL` is GPIO20 and `PIN_SDA` is GPIO21, which are module pads 30 and 31 on `U_ESP1`. |
| RST_SHUT pulldown | pulldown on pin 33 | Pin 33 has no net. No footprint is tied to it. |

`C_DISC`, `R_DSG1`, and the diode clusters are the old names most likely to be mistaken for the rows above. They are scored in the power-stage sections. Short version: `R_S1` / `R_S2` are the sense-filter resistors. `C_DISC` is a 10 µF bulk cap in the power column, about 15 mm left of `U_BQ2`, which is the wrong value and the wrong place for a REG pin. `R_DSG1` is the unnetted 100 Ω nearest `Q2`, so it reads as the discharge-gate resistor. The Schottkys beside the monitors (`D_PRI*`, `D_SEC*`) do not land on a BAT pin.

The photographs show a denser 0402 field around each monitor than this file contains, including a part marked `10R0` and small capacitors on the regulator side of a BQ76952 (IMG_2145, IMG_2146). Those parts are on the photographed VBMS. They are not extra footprints here. The same is true of the small resistors beside the USB connector (IMG_2149, IMG_2150).

## Monitors

### `U_BQ1` — known

BQ7695202, TQFP-48, front, centre (87.875, 13.875), rotation 0. Low stack, `CELL0`…`CELL16`. Photo IMG_2146 / IMG_2147 shows this QFP on the USB side of the inductor. 24 of 48 pins have a net. No pin has copper to another part.

| Pins | Function on the BQ76952 | Net on this board |
|---|---|---|
| 1–15 | VC15…VC1 | `BQ1_VC15`…`BQ1_VC1` |
| 16 | VC0 | `CELL0` |
| 17 | VSS | `GND` |
| 18 | SRP | `SRP` (same net name as `U_BQ2` pin 18) |
| 19 | NC | none |
| 20 | SRN | `SRN` (same net name as `U_BQ2` pin 20) |
| 21 | TS1 | `TS1` |
| 22 | TS2 / WAKE | `TS2` |
| 23 | TS3 | `TS3` |
| 24 | REG18 | none |
| 25 | HDQ / ALERT | none |
| 26 | SCL / SPI clock | none |
| 27 | SDA / SPI MISO | none |
| 28 | HDQ / SPI MOSI | none |
| 29 | CFETOFF / SPI CS | none |
| 30 | DFETOFF / BOTHOFF | none |
| 31 | DCHG | none |
| 32 | DDSG | none |
| 33 | RST_SHUT | none |
| 34 | REG2 | none |
| 35 | REG1 | none |
| 36 | REGIN | none |
| 37 | BREG | none |
| 38 | FUSE | none |
| 39 | PDSG | none |
| 40 | PCHG | none |
| 41 | LD | none |
| 42 | PACK | none |
| 43 | DSG | none |
| 44 | NC | none |
| 45 | CHG | none |
| 46 | CP1 | none |
| 47 | BAT | `BQ1_VC16` |
| 48 | VC16 | `BQ1_VC16` |

Pin 47 and pin 48 are one net. Firmware enables REG0 and sets REG1 to 3.3 V, and it configures pin 25 (`ALERT`), pin 28 (`HDQ`), pin 31 (`DCHG`), and the TS pins as thermistor inputs on the first monitor. Those pads exist. They have no net.

### `U_BQ2` — known

BQ7695202, TQFP-48, front, centre (44.775, 13.875), rotation 0. High stack, `CELL16`…`CELL32`. 22 of 48 pins have a net. No pin has copper.

Pins 1–20 and 47–48 match `U_BQ1`, with the `BQ2_` prefix, except pin 16 (`VC0`) is net `CELL16` and pins 47 and 48 (`BAT`, `VC16`) are both net `BQ2_VC16`. Pin 21 (`TS1`) is net `TS4`. Pins 22–46 have no net. `SRP` and `SRN` are the same net names used on `U_BQ1`, so the two sense inputs are tied together by name and still do not reach the shunt.

## Cell filter — known

`R_F1`–`R_F32` are 20 Ω, 0402, front, y = 30.3, rotation 0. X runs from 37.400 (`R_F1`) to 99.493 (`R_F32`) on a 2.003 mm pitch. Each one has copper from pad 1 to a cell jack. Pad 2 is the monitor-side net and has no copper. None of them reaches a BQ pin.

`C_F1`–`C_F32` are 0.22 µF, 0402, on the back, rotation 90. They have nets and no copper. They are the differential caps, including VC1-to-VC0.

| Ref | Cell side (has copper) | Monitor side (no copper) | Cap across those taps |
|---|---|---|---|
| `R_F1` | `CELL32` `J_CELL4.1` | `BQ2_VC16` | `C_F32` to `BQ2_VC15` |
| `R_F2` | `CELL31` `J_CELL4.2` | `BQ2_VC15` | `C_F31` to `BQ2_VC14` |
| `R_F3` | `CELL30` `J_CELL4.3` | `BQ2_VC14` | `C_F30` to `BQ2_VC13` |
| `R_F4` | `CELL29` `J_CELL4.4` | `BQ2_VC13` | `C_F29` to `BQ2_VC12` |
| `R_F5` | `CELL28` `J_CELL4.5` | `BQ2_VC12` | `C_F28` to `BQ2_VC11` |
| `R_F6` | `CELL27` `J_CELL4.6` | `BQ2_VC11` | `C_F27` to `BQ2_VC10` |
| `R_F7` | `CELL26` `J_CELL3.1` | `BQ2_VC10` | `C_F26` to `BQ2_VC9` |
| `R_F8` | `CELL25` `J_CELL3.2` | `BQ2_VC9` | `C_F25` to `BQ2_VC8` |
| `R_F9` | `CELL24` `J_CELL3.3` | `BQ2_VC8` | `C_F24` to `BQ2_VC7` |
| `R_F10` | `CELL23` `J_CELL3.4` | `BQ2_VC7` | `C_F23` to `BQ2_VC6` |
| `R_F11` | `CELL22` `J_CELL3.5` | `BQ2_VC6` | `C_F22` to `BQ2_VC5` |
| `R_F12` | `CELL21` `J_CELL3.6` | `BQ2_VC5` | `C_F21` to `BQ2_VC4` |
| `R_F13` | `CELL20` `J_CELL3.7` | `BQ2_VC4` | `C_F20` to `BQ2_VC3` |
| `R_F14` | `CELL19` `J_CELL3.8` | `BQ2_VC3` | `C_F19` to `BQ2_VC2` |
| `R_F15` | `CELL18` `J_CELL2.1` | `BQ2_VC2` | `C_F18` to `BQ2_VC1` |
| `R_F16` | `CELL17` `J_CELL2.2` | `BQ2_VC1` | `C_F17` to `CELL16` |
| `R_F17` | `CELL16` `J_CELL2.3` | `BQ1_VC16` | `C_F16` to `BQ1_VC15` |
| `R_F18` | `CELL15` `J_CELL2.4` | `BQ1_VC15` | `C_F15` to `BQ1_VC14` |
| `R_F19` | `CELL14` `J_CELL2.5` | `BQ1_VC14` | `C_F14` to `BQ1_VC13` |
| `R_F20` | `CELL13` `J_CELL2.6` | `BQ1_VC13` | `C_F13` to `BQ1_VC12` |
| `R_F21` | `CELL12` `J_CELL2.7` | `BQ1_VC12` | `C_F12` to `BQ1_VC11` |
| `R_F22` | `CELL11` `J_CELL2.8` | `BQ1_VC11` | `C_F11` to `BQ1_VC10` |
| `R_F23` | `CELL10` `J_CELL2.9` | `BQ1_VC10` | `C_F10` to `BQ1_VC9` |
| `R_F24` | `CELL9` `J_CELL1.1` | `BQ1_VC9` | `C_F9` to `BQ1_VC8` |
| `R_F25` | `CELL8` `J_CELL1.2` | `BQ1_VC8` | `C_F8` to `BQ1_VC7` |
| `R_F26` | `CELL7` `J_CELL1.3` | `BQ1_VC7` | `C_F7` to `BQ1_VC6` |
| `R_F27` | `CELL6` `J_CELL1.4` | `BQ1_VC6` | `C_F6` to `BQ1_VC5` |
| `R_F28` | `CELL5` `J_CELL1.5` | `BQ1_VC5` | `C_F5` to `BQ1_VC4` |
| `R_F29` | `CELL4` `J_CELL1.6` | `BQ1_VC4` | `C_F4` to `BQ1_VC3` |
| `R_F30` | `CELL3` `J_CELL1.7` | `BQ1_VC3` | `C_F3` to `BQ1_VC2` |
| `R_F31` | `CELL2` `J_CELL1.8` | `BQ1_VC2` | `C_F2` to `BQ1_VC1` |
| `R_F32` | `CELL1` `J_CELL1.9` | `BQ1_VC1` | `C_F1` to `CELL0` |

`C_F1`–`C_F8` sit under `U_BQ1` at y = 11.0, x = 80.0 then 81.9 on a 1.9 mm pitch. `C_F9`–`C_F16` are the second row at y = 13.2, same X pattern. `C_F17`–`C_F24` sit under `U_BQ2` at y = 11.0 starting at x = 37.0. `C_F25`–`C_F32` are at y = 13.2. All rotation 90, back.

`CELL0` (`J_CELL1` pad 10) has no `R_F`. That is the missing VC0 20 Ω.

## Bleed row — known

`R_B1`–`R_B33` are 27 Ω, 0805, front, rotation 90. They are the bleed resistors beside the cell connectors. Pads have no net and no copper. They stay on this row.

`R_B1`–`R_B32` are at y = 28.05. X starts at 36.375 and steps 2.003 mm, through `R_B32` at 98.468. `R_B33` is at (100.975, 28.025), a slightly wider gap at the end of the same row. Thirty-three resistors for thirty-two cells: the row is one longer than a single resistor per cell. Which tap the extra one belongs to is not on the pads.

## Pack, charge, and current sense

### Connectors and the fuse — known

| Ref | Value / footprint | Place | Pads | Job |
|---|---|---|---|---|
| `J_BAT1` | XT30PW-M | (5.2, 24.9) | 1 `CELL32` (silk TOP CELL), 2 `CELL0` (silk BOT) | Pack connector. Pad 1 has copper to `F1`. Pad 2 does not reach the shunt. |
| `J_CHG1` | XT30PW-F | (5.6, 7.0) | 1 `CHG+`, 2 `CHG−` | Charger connector. Nets only, no copper. |
| `F1` | JT 15A, fuse 2512 | (17.43, 27.48), rot 90 | 1 `CELL32`, 2 `CELL32_FUSED` | Pack fuse. IMG_2143 shows the white 15 A body. Copper only on the `CELL32` side, into `J_BAT1`. The fused side does not reach a FET drain. |

The value strings on `J_CELL*` (`0-8`, `9-16`, `17-24`, `25-32`) are group labels. The pad nets above are the taps.

### Shunt and the two 100 Ω resistors

| Ref | Value | Place | Pads | Call |
|---|---|---|---|---|
| `R_SH1` | `R001` (1 mΩ), 2512 | (14.0, 16.2), rot 90 | 1 `CELL0`, 2 `SHUNT_MID` | **known.** Pack-negative end of the sense resistor. IMG_2143 shows `R001` standing next to the battery XT30. No copper. |
| `R_SH2` | `R001` (1 mΩ), 2512 | (23.9, 15.8), rot 0 | 1 `SHUNT_MID`, 2 `CHG−` | **known.** Second 1 mΩ, in series. The pair is 2 mΩ, which is `HW_R_SHUNT` (0.0002 Ω) in the VBMS firmware. No copper from `SHUNT_MID` to `R_SH1`, and no copper to `SRP` / `SRN`. |
| `R_S1` | `1000` (100 Ω), 0805 | (17.63, 15.0) | none | **probable SRP/SRN filter resistor.** Sits on the shunt, between the two `R001` bodies. IMG_2143 shows the mark `1000` on both of these 0805s. 100 Ω is the EVM series value. |
| `R_S2` | `1000` (100 Ω), 0805 | (17.5, 17.0) | none | **probable**, the second series resistor of that filter. Same photo, same mark, stacked with `R_S1`. |
| `D_S1` | `TVS`, SOD-123 | (17.68, 20.85), rot −90 | none | **probable** clamp for the shunt or the pack negative. It is the SOD directly under `R_S2` in IMG_2143. Standoff voltage is not in the value field. |

The sense path the pads describe is `CELL0` — `R_SH1` — `SHUNT_MID` — `R_SH2` — `CHG−`, with `R_S1` and `R_S2` as the 100 Ω filters off those Kelvin points. The filter capacitor is not placed.

### Charge FET — known device, gate parts known from their nets

`Q1` is an AGM15T03LL, TOLL-8, (22.4, 7.3), rotation 0. N-channel 150 V MOSFET. IMG_2143 shows the large black package with the triangle logo between the charge XT30 and the relay. Drain tab is `CELL32_FUSED`. Pads 1, 2, 3, 5, 6, 7, and 8 are `CHG+`. Pad 4 is `Q1_GATE`. That is a high-side charge FET: drain on the fused pack positive, source on the charger positive. No copper. The AGM pin drawing was not in the local docs. The file treats pad 4 as the gate. Confirm that against the AGM15T03LL pin figure before wiring a different pad as the gate.

| Ref | Value | Place | Pads | Call |
|---|---|---|---|---|
| `R_G1` | `01X` (10 Ω), 0603 | (29.5, 7.6) | `Q1_GATE`, `SSR_OUT_CHG` | **known** series gate resistor, from the relay's charge output to the gate. |
| `R_SSR1` | `01X` (10 Ω), 0603 | (29.2, 4.05) | `SSR_OUT_CHG`, `Q1_GATE` | **known** as a second resistor on those same two nets. By net name it sits in parallel with `R_G1`. No copper joins them. |
| `R_GS1` | `474` (470 kΩ), 0603 | (29.5, 8.95) | `Q1_GATE`, `CHG+` | **known** gate-to-source resistor. Source of `Q1` is `CHG+`. IMG_2143 shows `474` in this cluster. |
| `R_SSR2` | `10k`, 0603 | (29.15, 5.7) | `Q1_GATE`, `GND` | **known** from the nets: 10 kΩ from the charge gate to logic ground. This is the only 10 kΩ footprint, so it is not a spare I2C pull-up or a thermistor bias. |
| `D_GS1` | PDZ16B, SOD-323 | (29.18, 10.85), rot 180 | `Q1_GATE`, `CHG+` | **known** 16 V gate-to-source zener. The photo shows the banded SOD in the same cluster. |

### Discharge FET

`Q2` is the second AGM15T03LL, (24.7, 24.9), rotation 180. Drain tab `CELL32_FUSED`. Pads 1, 2, 3, 5, 6, 7, and 8 are `PACK+`. Pad 4 is `Q2_GATE`. High-side discharge FET: drain on the fused pack positive, source on the pack output. IMG_2143 shows this package beside the shunt, triangle logo visible. No copper. Same gate-pad question as `Q1`.

`Q2_GATE` meets no other footprint. The schematic symbol `R_G2` (100 Ω, meant for this gate) is not on the board.

`R_DSG1` — **probable** discharge-gate resistor. Value `1000` (100 Ω), 0805, (30.78, 29.83), rotation 90, no net. It is the 100 Ω on the connector edge just left of `R_F1` and below `Q2`. It is not the sense filter: that pair is `R_S1` / `R_S2`, up by the shunt. It is not a BQ input resistor: those are the 20 Ω `R_F` row, and this part is 100 Ω.

`FB1` — **unknown**. Value `Unmarked`, 0603 footprint, (30.9, 26.58), rotation 90, no net. It sits between `Q2` and the bleed row. The photo of that neighbourhood shows `000` (0 Ω) jumpers among the gate parts. This footprint is the one whose value was left unread. Job not assigned.

### Charge-port diodes — probable

These four sit in the strip between the two XT30s. IMG_2143 shows three black SOD-123F parts in a row under the `CHG −` silk, a small resistor at the end of that row, and the beige 1812 next to the vertical shunt. No nets.

| Ref | Value | Place | Call |
|---|---|---|---|
| `D_CHG1` | DSK320, SOD-123F | (2.70, 15.73), rot −90 | **probable** charge-path Schottky. Three of them, same package, same orientation, at the charger end. |
| `D_CHG2` | DSK320, SOD-123F | (4.88, 15.65), rot −90 | **probable**, same row. |
| `D_CHG3` | DSK320, SOD-123F | (6.75, 15.80), rot −90 | **probable**, same row. |
| `R_CHG1` | `100k`, 0603 | (0.90, 15.70), rot 90 | **probable** resistor for that diode row. The photo mark on the part at the end of the row reads as a 100 kΩ code, which matches the value field. It is not the firmware's 220 kΩ / 4.7 kΩ divider. |
| `C_FLT1` | `10uF_100V`, 1812 | (10.175, 16.625), rot 90 | **probable** high-voltage capacitor at the shunt / charge-diode end. It is not next to `U4`. A 100 V rating is below a 32-series pack at 4.2 V per cell (about 134 V) if this cap is across the pack. Value left as stored. |

### Relay — known device, pin jobs are the pad names

`U_SSR1` value `GSRELAY`, footprint `H2440_SSR`, 8-pad SOIC, (36.7, 3.5), rotation 180. The project readme calls this part an H2440. IMG_2143 shows the SOIC above `Q1`. No SOIC pinout for an H2440 was found, so the functions below are the pad nets, not a datasheet check. Confirm the pinout before treating pad 7 or pad 8 as a FET driver.

| Pad | Net | Copper |
|---|---|---|
| 1 | `PIN_CHG_EN` | none |
| 2 | `PIN_OUT_EN` | none |
| 3 | `PIN_PSW_EN` | none |
| 4 | `GND` | to `C_SSR1` and `C_SSR2` |
| 5 | `VBOOST` | to `C_SSR1` and `C_SSR2` |
| 6 | `CELL32` | none |
| 7 | `SSR_OUT_DSG` | none |
| 8 | `SSR_OUT_CHG` | none |

Firmware uses those three enable names on GPIOs, plus two more that are not on this chip: `PIN_PCHG_EN` (GPIO8, module pad 22) and `PIN_COM_EN` (GPIO9, module pad 23). `PIN_COM_EN` is what the firmware toggles to disconnect one monitor while it changes the other's I2C address. No footprint is netted to `PIN_COM_EN` or `PIN_PCHG_EN`.

`C_SSR1` — **known**. 100 nF, 0603, (28.45, 1.75), rot 90. Pads `VBOOST` and `GND`, copper to `U_SSR1` and to `C_SSR2`.

`C_SSR2` — **known**. 1 µF, 0805, (30.0, 1.7), rot 90. Same two nets, same copper.

`C_DISC` — **probable** bulk capacitor in the power column, **unknown** as a BQ part. 10 µF, 1206, (30.1, 14.1), rot 90, no net. It sits on the chip's midline, about 15 mm left of `U_BQ2`, in the column with the charge-gate parts and `R_SEC1`. A REG18 or REG1 capacitor is typically 1–2.2 µF and sits on pin 24 or pin 35. This part is the wrong value and the wrong place for those pins, and it is not on the BAT pin (pin 47 is on the small-Y edge of the QFP).

## Diodes beside the monitors — unknown

Six Schottkys, SOD-123, value `D_Schottky`, no nets. Each monitor has a pair on its XT30 side and a single diode on its USB side. They are the cluster most easily read as a BAT-pin diode. Nothing in the nets, the value, or a one-per-chip count ties one of them to pin 47.

| Ref | Place | Sits |
|---|---|---|
| `D_SEC2` | (32.78, 17.58), rot −90 | Pair, XT30 side of `U_BQ2` |
| `D_SEC1` | (35.13, 17.55), rot −90 | Pair, XT30 side of `U_BQ2` |
| `D_SEC3` | (52.20, 17.30), rot −90 | Single, USB side of `U_BQ2` |
| `D_PRI2` | (74.80, 17.45), rot −90 | Pair, XT30 side of `U_BQ1`, under the buck |
| `D_PRI1` | (77.25, 17.38), rot −90 | Pair, XT30 side of `U_BQ1` |
| `D_PRI3` | (99.18, 15.38), rot 180 | Single, between `U_BQ1` and `U_ESP1` |

`R_SEC1` — **unknown**. `01X` (10 Ω if the EIA-96 reading holds), 0603, (29.75, 17.2), no net. It is the resistor immediately beside `D_SEC1` / `D_SEC2`. A 10 Ω next to that pair could be their series element. It is not assigned to VC0 or to BAT: VC0 wants 20 Ω, and this part is 15 mm from `U_BQ2` pin 16.

`R_CHG2` — **probable** charge-voltage divider, high side. `2203` (220 kΩ), 0805, (15.2, 1.1), no net. It is on the logic edge by the charge XT30. Firmware `HW_GET_VCHG()` divides with 220 kΩ over 4.7 kΩ into ESP ADC1 channel 0 (GPIO0, module pad 12). The matching 4.7 kΩ is not a value on any footprint, and the same firmware wants a second identical divider for the pack output (`HW_GET_VOUT()`, GPIO1, module pad 13). Only one 220 kΩ is placed.

## Logic supply — known chip, surrounding parts probable

The buck is the group at the logic edge between the two monitors. IMG_2146 shows the shielded inductor, the yellow `107C` tantalum, a SOD diode, and an MSOP marked `7138`.

`U4` — **known** LTC7138, MSOP-16 with the four pins that package omits, (60.2, 5.93), rotation −90. All pads unnetted, including the exposed pad. The placed pins are the ones this regulator has:

| Pad | LTC7138 function |
|---|---|
| 1 | SW, to the inductor and the catch-diode cathode |
| 3 | VIN |
| 5 | FBO (used when paralleling a second LTC7138; only one is placed) |
| 6 | VPRG2 |
| 7 | VPRG1 |
| 8 | GND |
| 9 | VFB |
| 10 | SS |
| 11 | ISET |
| 12 | OVLO |
| 14 | RUN |
| 16 | ANODE, catch-diode anode sense |
| 17 | exposed pad, GND |

Fixed 3.3 V or 5 V is selected by tying VPRG1 / VPRG2 to SS or GND. No resistor is required for that. An adjustable output would need a divider on pin 9, and no divider is placed at the IC.

| Ref | Value | Place | Call |
|---|---|---|---|
| `L1` | `180uH_181`, 7.3 mm inductor | (69.34, 6.6) | **probable** buck inductor. Sits on the USB side of `U4`, between the switch node and `C_TAN1`. The datasheet example uses 220 µH; the placed value is 180 µH. |
| `D_BST1` | `Schottky`, SOD-123 | (63.78, 5.03), rot −90 | **probable** catch diode. It is the SOD between `U4` pin 1 (SW) and `L1`. Cathode toward SW, anode toward pin 16, is the LTC7138 connection. Pads have no net, so the direction is not confirmed in copper. |
| `C_TAN1` | `100uF_16V`, EIA-6032 tantalum | (75.9, 5.0), rot 90 | **probable** buck output capacitor. The yellow body in IMG_2146 is marked `107C` (100 µF, 16 V). |

`C_FLT1` is the other capacitor sometimes grouped with this buck. It is physically at the shunt. See the charge-port section.

## ESP32, USB, CAN, temperatures, buzzer

### `U_ESP1` — known

ESP32-C3-MINI-1, (108.4, 8.6), rotation 0. Every pad is unnetted, including the ground pad. IMG_2149 shows the Espressif module and the silk `VBMS Mini32 V1.2`. The schematic symbol is the bare ESP32-C3, whose pin numbers are not the module pad numbers. The module pads the VBMS firmware uses are all present:

| Module pad | Name | Firmware use |
|---|---|---|
| 3 | 3V3 | logic supply |
| 5 | GPIO2 | `PIN_ENABLE`. Also a strapping pin. |
| 8 | EN | chip enable. Espressif says this pad must not float. No pull-up and no switch are placed. |
| 12 | GPIO0 | charge-voltage ADC (`HW_ADC_CH0`) |
| 13 | GPIO1 | output-voltage ADC (`HW_ADC_CH1`) |
| 16 | GPIO10 | `PIN_PSW_EN` |
| 18 | GPIO4 | `PIN_OUT_EN` |
| 19 | GPIO5 | `PIN_CHG_EN` |
| 20 | GPIO6 | CAN RX |
| 21 | GPIO7 | CAN TX |
| 22 | GPIO8 | `PIN_PCHG_EN`. Strapping pin. |
| 23 | GPIO9 | `PIN_COM_EN`. Strapping pin, default weak pull-up. |
| 26 | GPIO18 | USB D− |
| 27 | GPIO19 | USB D+ |
| 30 | GPIO20 | I2C SCL |
| 31 | GPIO21 | I2C SDA |
| 1, 2, 11, 14, 36–53 | GND | ground pad and ground pins |
| 49 | exposed pad | ground |

Pads 4, 7, 9, 10, 15, 17, 24, 25, 28, 29, and 32–35 are NC on the module.

Silk `EN` is text at (126.8, 24), on the connector edge past `J_T1`. It is not a footprint. There is no enable switch on the board. Firmware `PIN_ENABLE` is GPIO2 (pad 5), which is a different pin from chip-enable pad 8.

### `J_USB1` — known

USB-C receptacle, 16-pin, (124.6, 4.11), rotation 180. All signal pads and the shell are unnetted. IMG_2149 and IMG_2150 show the connector at the end of the board, next to the module. A6/B6 are D+, A7/B7 are D−, A4/B4 and A9/B9 are VBUS and CC. No series resistors are placed at the receptacle. The module USB pins are pads 26 and 27.

### `U7` — known

ISO1050, footprint is the wide 8-pin DIP outline used for the DUB package, (123.8, 14.2), rotation 0. IMG_2150 shows the SOIC under the USB connector. Nets match the ISO1050 pinout. No copper.

| Pad | ISO1050 | Net |
|---|---|---|
| 1 | VCC1 | `+3V3` |
| 2 | RXD | `CAN_RX` |
| 3 | TXD | `CAN_TX` |
| 4 | GND1 | `GND` |
| 5 | GND2 | `ISO_GND` |
| 6 | CANL | `CANL` |
| 7 | CANH | `CANH` |
| 8 | VCC2 | `5VExt` |

### `J_COMM1` — known

JST GH 1×4, (34.1, 22.8). Pads: 1 `CANH`, 2 `CANL`, 3 `ISO_GND`, 4 `5VExt`. Silk `5VExt GND CANL CANH`. No copper. This is the ESC CAN and 5 V connector. The isolated side of `U7` uses the same net names.

### Thermistor connectors — known

JST GH 1×2, y = 22.8, no copper. The return pad on each one is net `GND`.

| Ref | Place | Signal pad |
|---|---|---|
| `J_T1` | (122.0, 22.8) | `TS1` |
| `J_T2` | (115.0, 22.8) | `TS2` |
| `J_T3` | (108.0, 22.8) | `TS3` |
| `J_T4` | (101.0, 22.8) | `TS4` |

`TS1`, `TS2`, and `TS3` are also the nets on `U_BQ1` pins 21–23. `TS4` is the net on `U_BQ2` pin 21, which is that chip's TS1 pin. No bias resistor is placed at the connectors. The firmware's NTC math assumes the BQ's internal 18 kΩ to 1.8 V, and it subtracts 500 Ω inside the conversion. No footprint is stored as 500 Ω or 18 kΩ.

### Cell connectors — known

JST GH, vertical, y = 22.8, rotation 0. Each signal pad has copper to the cell side of one `R_F`, except `J_CELL1` pad 10 (`CELL0`), which has a net and no copper. Silk group text (`0- CELLS 8+` and so on) is approximate. The pad nets are the taps. Left to right along the board is `J_CELL4` … `J_CELL1`, `CELL32` down to `CELL0`.

| Ref | Value label | Place | Pads, from pad 1 |
|---|---|---|---|
| `J_CELL4` | `25-32` | (44.3, 22.8) | `CELL32` `CELL31` `CELL30` `CELL29` `CELL28` `CELL27` |
| `J_CELL3` | `17-24` | (57.4, 22.8) | `CELL26` `CELL25` `CELL24` `CELL23` `CELL22` `CELL21` `CELL20` `CELL19` |
| `J_CELL2` | `9-16` | (72.6, 22.8) | `CELL18` `CELL17` `CELL16` `CELL15` `CELL14` `CELL13` `CELL12` `CELL11` `CELL10` |
| `J_CELL1` | `0-8` | (89.0, 22.8) | `CELL9` `CELL8` `CELL7` `CELL6` `CELL5` `CELL4` `CELL3` `CELL2` `CELL1` `CELL0` |

### `BZ1` — known

Buzzer, value `FUET-5030`, 5 mm, (88.3, 2.8), rotation 0. On the logic edge above `U_BQ1`. IMG_2146 and IMG_2147 show the round can. Pad 1 `+3V3`, pad 2 `BUZZ_LOW`, pad 3 no net. No copper. The lisp beeper toggles a PWM output. The low-side switch for `BUZZ_LOW` is not on the board.

## On the schematic, not on the board

`Q_BZ1` is a schematic symbol valued as a small MOSFET for the buzzer. It has no footprint.
`R_G2` is a schematic symbol, 100 Ω, for the `Q2` gate. It has no footprint. `R_DSG1` is the placed 100 Ω near that FET, and it has no schematic symbol.

`U4`, `L1`, `D_BST1`, `C_TAN1`, `C_DISC`, `C_FLT1`, `J_USB1`, `R_S1`, `R_S2`, `R_DSG1`, `R_SEC1`, `R_CHG2`, `R_GS1`, `FB1`, `D_PRI1`–`D_PRI3`, `D_SEC1`–`D_SEC3`, `D_S1`, and `R_B1`–`R_B32` are footprints with no schematic symbol. `R_B33` does have one. The pad nets in this file are the working copy.

## Open points before the next wiring pass

- `U_SSR1`: eight pads are present. A datasheet pinout for the H2440 / GSRELAY was not found. Pads 7 and 8 are named `SSR_OUT_DSG` and `SSR_OUT_CHG` in the file. Confirm those functions before connecting them to `Q2` or `Q1`.
- `Q1` and `Q2`: the file treats TOLL pad 4 as the gate. Confirm that against the AGM15T03LL drawing.
- `U_ESP1` pad 8 is CHIP_EN and has no pull-up and no switch.
- No placed part is the VC0 20 Ω, the BAT-pin resistor, a regulator capacitor, the SRP/SRN capacitor, an I2C pull-up, or the `PIN_COM_EN` / `PIN_PCHG_EN` switch.
