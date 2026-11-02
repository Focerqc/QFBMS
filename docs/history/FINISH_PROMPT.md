> Historical snapshot from before the 2026-11-02 repository split.
> May contain conflicting or unverified electrical instructions; not current editing guidance.

Finish `qfbms32 ai pcb/` on the parts that are already placed. The board is finished when those parts measure the 32 cells, sense pack current, read the thermistors, let the ESP talk to both monitors, and switch charge and discharge. A silk screen that matches the photos, with nets that do not do that, is not finished.

PCB pad nets on `qfbms32.kicad_pcb` are the working copy. Leave the schematic alone. Do not commit. Do not run scripts in `qfbms32 ai pcb/scratch/`. KiCad Python is `C:\Program Files\KiCad\10.0\bin\python.exe`. Score with `python _tools/progress_dashboard/server.py` at http://localhost:5181 and reload after each save.

## What wins

1. Photos in `qfbms32 ai pcb/_reference/user_photos/`. `IMG_2151.png` is the back. It has copper, silk, and through-holes. It has no parts.
2. Footprints already on the front, checked against `IMG_2143`–`IMG_2150`.
3. External nets in `WORKING_TOPOLOGY.md`, except the line that puts `C_F*` on B.Cu under each BQ. That line is wrong.
4. TI BQ76952 docs, for values and pin function only.

The placed chip stays when it is the wrong package for the eval board: ESP32-C3-MINI-1, AGM15T03LL, H2440, and the 27 Ω `R_B*` row.

## Do not

- Put a footprint on the back. Copper on B.Cu is fine. A part on B.Cu is not.
- Leave `C_F1`–`C_F32` under either QFP. They are 0.22 µF 0402s that were parked on the back at y = 11.0 and y = 13.2, through exposed pad 49 and its thermal vias. Move only those 32 refs to the front, beside the monitor they serve, clear of the package, the exposed pad, and the thermal vias. Match the 0402 field in `IMG_2145`, `IMG_2146`, and `IMG_2147`. If a cap has no open front site, stop and name the ref. Do not put it on the die pad or the back.
- Move, rotate, or replace any other footprint. `R_B1`–`R_B33` stay at y ≈ 28.05 mm, rotation 90.
- Add a part. These jobs have no footprint: VC0 series 20 Ω, BAT-pin resistor and cap, REG18 / REG1 / REG2 / REGIN / BREG caps, CP1 cap, SRP/SRN capacitor, I2C pull-ups, enable switch, buzzer MOSFET. Report the ref and the pin. Do not invent a footprint.
- Change a value.
- Use a maze router. Place each net on a path you can name. If that copper fails clearance, tag the ref SKIPPED, record the copper that blocked it, and move on. Do not retry a failed path. Do not delete a net that already cleared. Save after every net that passes, then re-score.

Netclass clearance is 0.127 mm. Track width 0.2 mm. Via drill 0.3 mm, diameter 0.6 mm. A 0.2 mm track fits in an `R_B` gap. A 0.6 mm via does not. Do not put a via inside an `R_B` pad. Hole clearance and hole-to-hole are 0.25 mm. Copper-to-edge is 0.35 mm.

## Nets to correct before any new track

- `U_BQ1` pin 47 = `BQ1_BAT`. `U_BQ2` pin 47 = `BQ2_BAT`. Pin 48 stays `BQ1_VC16` and `BQ2_VC16`. Do not tie the two BAT nets together. No resistor exists between pin 47 and pin 48. Do not add one.
- AGM15T03LL: pad 1 is the gate, pads 2–8 are the source, the tab is the drain. `Q1` pad 1 = `Q1_GATE`. `Q1` pad 4 = `CHG+`. `Q2` pad 1 = `Q2_GATE`. `Q2` pad 4 = `PACK+`. Pads 2, 3, 5, 6, 7, and 8 stay on the source net they already have. The tab stays `CELL32_FUSED`.
- Leave `U_SSR1` pads 7 and 8 unconnected. Pads 4 and 5 already reach the boost caps. The H2440 pinout for the gate outputs is not confirmed.

Save this net edit before any tracks.

## Cell filters

`R_F1`–`R_F32` are the 20 Ω 0402s on the front at y = 30.3. Pad 1 already has copper to the cell jack. Pad 2 is the monitor net and has no copper. Map:

| Ref | Pad 2 | Cap, after it is on the front |
|---|---|---|
| `R_F1` | `BQ2_VC16` | `C_F32` to `BQ2_VC15` |
| `R_F2` | `BQ2_VC15` | `C_F31` to `BQ2_VC14` |
| `R_F3` | `BQ2_VC14` | `C_F30` to `BQ2_VC13` |
| `R_F4` | `BQ2_VC13` | `C_F29` to `BQ2_VC12` |
| `R_F5` | `BQ2_VC12` | `C_F28` to `BQ2_VC11` |
| `R_F6` | `BQ2_VC11` | `C_F27` to `BQ2_VC10` |
| `R_F7` | `BQ2_VC10` | `C_F26` to `BQ2_VC9` |
| `R_F8` | `BQ2_VC9` | `C_F25` to `BQ2_VC8` |
| `R_F9` | `BQ2_VC8` | `C_F24` to `BQ2_VC7` |
| `R_F10` | `BQ2_VC7` | `C_F23` to `BQ2_VC6` |
| `R_F11` | `BQ2_VC6` | `C_F22` to `BQ2_VC5` |
| `R_F12` | `BQ2_VC5` | `C_F21` to `BQ2_VC4` |
| `R_F13` | `BQ2_VC4` | `C_F20` to `BQ2_VC3` |
| `R_F14` | `BQ2_VC3` | `C_F19` to `BQ2_VC2` |
| `R_F15` | `BQ2_VC2` | `C_F18` to `BQ2_VC1` |
| `R_F16` | `BQ2_VC1` | `C_F17` to `CELL16` |
| `R_F17` | `BQ1_VC16` | `C_F16` to `BQ1_VC15` |
| `R_F18` | `BQ1_VC15` | `C_F15` to `BQ1_VC14` |
| `R_F19` | `BQ1_VC14` | `C_F14` to `BQ1_VC13` |
| `R_F20` | `BQ1_VC13` | `C_F13` to `BQ1_VC12` |
| `R_F21` | `BQ1_VC12` | `C_F12` to `BQ1_VC11` |
| `R_F22` | `BQ1_VC11` | `C_F11` to `BQ1_VC10` |
| `R_F23` | `BQ1_VC10` | `C_F10` to `BQ1_VC9` |
| `R_F24` | `BQ1_VC9` | `C_F9` to `BQ1_VC8` |
| `R_F25` | `BQ1_VC8` | `C_F8` to `BQ1_VC7` |
| `R_F26` | `BQ1_VC7` | `C_F7` to `BQ1_VC6` |
| `R_F27` | `BQ1_VC6` | `C_F6` to `BQ1_VC5` |
| `R_F28` | `BQ1_VC5` | `C_F5` to `BQ1_VC4` |
| `R_F29` | `BQ1_VC4` | `C_F4` to `BQ1_VC3` |
| `R_F30` | `BQ1_VC3` | `C_F3` to `BQ1_VC2` |
| `R_F31` | `BQ1_VC2` | `C_F2` to `BQ1_VC1` |
| `R_F32` | `BQ1_VC1` | `C_F1` to `CELL0` |

`U_BQ1` pin 16 stays `CELL0`. `U_BQ2` pin 16 stays `CELL16`. After the caps are on the front, connect each `R_F` pad 2 to both pads of its cap net and to that net's BQ pin. Connect `C_F1`'s `CELL0` pad to `U_BQ1` pin 16. Connect `C_F17`'s `CELL16` pad to `U_BQ2` pin 16.

Front cell tracks already run near y = 27.5 mm, including a 0.8 mm `CELL32` horizontal. Cross that row on the back. Bring the net to the front again before it reaches a front-side cap or a BQ pin.

## Then the rest of the placed parts

Route only pads that already exist.

- Pack path: `J_BAT1` pad 1 `CELL32` already reaches `F1`. Continue `F1` pad 2 `CELL32_FUSED` to both FET drain tabs. `J_BAT1` pad 2 is `CELL0`.
- Charge path: `J_CHG1` pad 1 `CHG+` to the `Q1` source pads. Pad 2 is `CHG−`.
- Sense: `CELL0` — `R_SH1` — `SHUNT_MID` — `R_SH2` — `CHG−`. `R_S1` and `R_S2` are the 100 Ω filters off those Kelvin points. Take them to `SRP` and `SRN` on both monitors. The filter capacitor is not placed. Do not add it.
- Temps: `J_T1`–`J_T4` pad 1 is `TS1`–`TS4`, pad 2 is `GND`. `TS1`–`TS3` are `U_BQ1` pins 21–23. `TS4` is `U_BQ2` pin 21. No bias resistor is placed. The firmware uses the BQ's internal pull-up. Do not add a 10 kΩ.
- `J_COMM1` and `U7` already share `CANH`, `CANL`, `ISO_GND`, and `5VExt` by name. Connect them in copper.
- `U4`, `L1`, `D_BST1`, `C_TAN1` are the buck. Net the pins that are on those footprints. `C_FLT1` is at the shunt, not next to `U4`. Leave its value. Do not call it a REG cap.
- `U_ESP1` is the ESP32-C3-MINI-1. I2C is GPIO20 / GPIO21 on module pads 30 and 31. Both monitors' pins 26 and 27 are SCL and SDA and are empty. Connect those four pins to the module. No pull-up is placed.
- `BZ1` pad 1 is `+3V3`, pad 2 is `BUZZ_LOW`. The low-side switch is not on the board. Connect the 3V3 pad to the buck rail. Report `BUZZ_LOW` as open.
- `R_B*` stay unnetted. The monitors balance through the VC pins. Do not slide them.

Do not route `U_SSR1` pads 7 or 8. Do not guess a gate drive from the BQ `CHG` / `DSG` pins onto the FET gates unless the placed gate parts (`R_G1`, `R_GS1`, `D_GS1`, `R_DSG1`) already sit on that net. `R_G2` is a schematic symbol with no footprint.

## Report

Reload the dashboard. Report pin 47 nets, where each `C_F` moved, which `R_F` pad reaches which cap and which BQ pin, which refs were skipped and what copper blocked them, which jobs have no placed part, and confirm zero footprints remain on the back.
