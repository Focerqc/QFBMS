> Historical snapshot from before the 2026-11-02 repository split.
> May contain conflicting or unverified electrical instructions; not current editing guidance.

# qfbms32

32-series BMS for a Fungineers pack. The board is a long strip, about 130 × 32 mm, two layers.

The parts are already placed to match the photos in `_reference/user_photos/`. Those positions, rotations, and packages stay. The work left is electrical: the placed parts have to do the BMS job.

## The job

The pack harness is `_reference/vfbms32_wiring_32s_best.jpg`. That drawing says which wire lands where. It is not a schematic.

| What the pack needs | On this board |
|---|---|
| Pack positive and negative | `J_BAT1` — TOP CELL is `CELL32`, BOT is `CELL0` |
| Charger | `J_CHG1` — `CHG+` / `CHG−` |
| 32 series cells, 33 taps | `J_CELL4` … `J_CELL1`, left to right `CELL32` … `CELL0` |
| Four thermistors | `J_T1` … `J_T4` |
| ESC CAN and 5 V | `J_COMM1`, through the isolator `U7` |
| Enable, buzzer, USB | Have to exist as a circuit, not only as a picture on the harness sheet |

Behind those connectors the board has to:

- Measure every cell on two BQ7695202s. `U_BQ1` is the low 16 (`CELL0`…`CELL16`). `U_BQ2` is the high 16 (`CELL16`…`CELL32`).
- Measure pack current on the shunt (`R_SH1`, `R_SH2`) through `SRP` / `SRN`.
- Bias and read the thermistors.
- Let the ESP32-C3 (`U_ESP1`) talk to both monitors.
- Switch charge (`Q1`) and discharge (`Q2`). `U_SSR1` is the gate helper that is actually placed. The BQ charge and discharge pins can drive gates too, once they are wired.
- Power the logic. `U4` is the buck that is placed for that.

The TI BQ76952 datasheet and EVM (under `_reference/ti_bq76952/`) supply pin function and the usual values: 20 Ω and 0.22 µF on each cell input, regulator caps, a sense filter, 10 kΩ thermistor bias. Use those values on the parts that are already here. Do not move a part to make the eval-board layout fit.

The placed chip stays even when it is a different part than the reference. `U_ESP1` is an ESP32-C3-MINI-1. The FETs are AGM15T03LL. The relay is an H2440. `R_B1`–`R_B33` are the 27 Ω bleed row beside the cell connectors. If a placed part has no pin for a function the reference wanted, stop and say which ref and which pin.

## Where it stands

This folder is the only copy of the board. Scored from the PCB file, not from notes. Open the progress dashboard and hit Reload after the board changes:

```powershell
python _tools/progress_dashboard/server.py
# http://localhost:5181
```

As of 27 Oct 2026 the file says:

- Connector names for pack, charge, the 33 cell taps, the four temps, and CAN match the harness.
- All 32 cell taps share copper with their filter resistor (`R_F`, 20 Ω). None of those resistors reach a BQ pin. The 0.22 µF caps (`C_F`) are on the back with nets and no copper.
- `U_BQ1` has 24 of 48 pins named. `U_BQ2` has 22. No BQ pin has copper to another part. Regulator, I2C, and the BQ FET-driver pins are empty. `BAT` is shorted to the `VC16` net. `VC0` on `U_BQ1` is tied straight to `CELL0`.
- The fuse input shares copper with TOP CELL. The fuse does not reach the FET drains. The shunt does not reach `SRP` / `SRN`. Neither FET gate reaches a driver.
- `U_ESP1`, USB-C, and the buck have no nets. There is no enable switch. The buzzer has a net name and nothing driving it.
- `R_B1`–`R_B33` are placed and unnetted. Leave them where they are.

The PCB pad nets are the working copy. The schematic has labels for the same idea and is not ahead of the board.

## Files

| Path | What it is |
|---|---|
| `qfbms32.kicad_pro` | KiCad 10 project |
| `qfbms32.kicad_pcb` | Layout. This is the board. |
| `qfbms32.kicad_sch` | Schematic |
| `WORKING_TOPOLOGY.md` | Net names for the harness and the two monitors |
| `qfbms.pretty/` | Footprints that are not in KiCad stock |
| `_reference/vfbms32_wiring_32s_best.jpg` | Pack harness drawing |
| `_reference/user_photos/` | The placed board, which the footprints have to match |
| `_reference/ti_bq76952/` | Datasheet, EVM guide, TIDA-010208 |
| `.history/` | Copies taken before large edits |
| `scratch/` | One-off scripts and the AGM pinout notes. Not part of the design. |

## Editing

Do not move, rotate, or swap a footprint to copy TI, to open a routing channel, or because the part looks unused. Route around it. Ask before a position, a footprint, or a value changes. The same rule is in `.cursor/rules/qfbms32-placement.mdc`.

KiCad's Python, for anything that imports `pcbnew`:

```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" script.py
```

The other local tool, board boxes, is the placement viewer on port 5180 (`python _tools/pcb_dashboard/server.py`). It does not score whether the circuit works.
