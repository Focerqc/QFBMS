> Historical snapshot from before the 2026-11-02 repository split.
> May contain conflicting or unverified electrical instructions; not current editing guidance.
>
> Superseded by the [current build plan](../../PLAN.md) and [design rules](../../DESIGN_RULES.md).
> The active design is charge-only. Discharge-switching instructions, blanket placement locks, and pin assignments below are preserved history, not the current specification.

# qfbms32 working topology

External wiring follows `_reference/vfbms32_wiring_32s_best.jpg`.
AFE passives follow `_reference/ti_bq76952` (BQ76952EVM / TIDA-010208).

Placement on `qfbms32.kicad_pcb` wins over both of those. TI values and pin functions do not move, rotate, or replace a footprint. The placed chip stays even when it is the wrong part for the reference (module vs bare QFN, AGM15T03LL, H2440, the 0805 `R_B*` row). If a placed chip cannot do the reference function, ask. Do not relocate neighbors to make the reference fit. See `.cursor/rules/qfbms32-placement.mdc`.

## External map (wiring diagram → board)

| Diagram | Board | Net(s) |
|---------|--------|--------|
| TOP_CELL (B+) | `J_BAT1` pad 1 (silk TOP CELL) | `TOP_CELL` (= `CELL32`) |
| BOT (B−) | `J_BAT1` pad 2 (silk BOT) | `BOT` (= `CELL0` / pack PGND sense) |
| CHG+ | `J_CHG1` pad 1 (silk CHG +) | `CHG+` |
| CHG− | `J_CHG1` pad 2 (silk CHG −) | `CHG−` |
| Cells (33 taps) | `J_CELL4`→`J_CELL1` pads by ascending X | `CELL32`…`CELL0` (silk group text is approximate) |
| Temp 1–4 | `J_T1`–`J_T4` | `TS1`…`TS4` + `GND`/`VSS` bias return |
| ESC CAN/5V | `J_COMM1` | `CANH`, `CANL`, `ISO_GND`, `5VExt` |
| USB-C | `J_USB1` | USB / ESP programming |

ESC power in the diagram splices to **TOP_CELL** and **BOT** externally (not a third XT30).

Cell-sense pad count 10+9+8+6 = **33** → `CELL0`…`CELL32`.

## Power stage (working, TI-ish high-side)

- `Q1` = CHG FET near `J_CHG1`
- `Q2` = DSG / pack-path FET near `J_BAT1`
- `R_SH1` / `R_SH2` = pack current sense (`SRP`/`SRN` domain)
- `U_SSR1` = precharge / gate helper (`VBOOST`, `VBAT_S`, `OUT_CHG`, …)
- `C_SSR1` (100nF) + `C_SSR2` (1µF) = **`VBOOST`–`GND` decoupling** next to SSR

## Dual BQ76952

| IC | Ref | Cells |
|----|-----|-------|
| IC1 lower 16S | `U_BQ1` | `CELL0`…`CELL16` → VC0…VC16 |
| IC2 upper 16S | `U_BQ2` | `CELL16`…`CELL32` → VC0…VC16 |

## TI passive targets (per AFE)

| Role | Value | Board action |
|------|-------|--------------|
| Cell input series R | **20 Ω** | `R_F1`–`R_F32` (was 100R) |
| Cell differential C | **0.22 µF** | `C_F1`–`C_F32` on **B.Cu** under each BQ |
| Decoupling | 0.1 µF | near REG/BAT as added |
| Balance | internal via VC + series R | `R_B*` kept for now (clone bleed); may DNP later |

Hold fixed: XT30 BAT/CHG, `J_CELL1–4`, `J_COMM1`, `J_T1–4`, USB-C unless a move is required and called out.

## Layout notes (2026-10-27)

- `R_B1`–`R_B33` stay on the committed pixel-matched row (y≈28.05, 90°). Do not park or respacing them.
- Schematic core (BQ/SSR/FET/connectors) now labeled to match these nets; use symbol **Y-flip** (`sy - local_y`) when scripting stubs.
- Filter VC fanout (R_F → via → B.Cu → `C_F` / BQ pads) is next on the PCB after CELL stubs are clean in DRC.
