# TI BQ76952 reference (electrical source of truth)

For the **working** fork, cell-monitor / AFE circuitry follows TI — not pixel-matching the clone passives.

## Local files

| File | What |
|------|------|
| `bq76952_datasheet.pdf` | Device datasheet (pinout, typical app, abs max) |
| `BQ76952EVM_users_guide_sluuc33a.pdf` | EVM user’s guide — **schematics §5.4**, BOM §5.2, layout |
| `TIDA-010208_design_guide_tiduey5.pdf` | 10s–16s pack ref design (high-side FETs, aux power, e-bike-ish) |

## EVM board / CAD files

- `SLUC687A.zip` — BQ76952EVM board files (Rev. A)
- Extracted under `SLUC687A/` (schematics, PCB, Gerbers, etc.)

## Primary circuit cues (from EVM BOM)

Per BQ IC (16S half of our dual-BQ board):

| Role | EVM typical |
|------|-------------|
| Cell input series R | **20 Ω** (1206 on EVM; we may use smaller pkgs if dissipation OK) |
| Cell differential C | **0.22 µF** |
| Assorted decoupling | **0.1 µF** near rails / digital |
| Thermistor bias | **10 kΩ** |
| Sense resistor (pack) | **1 mΩ** on EVM (our pack may keep clone sense if already sized) |

Schematic pages in the EVM guide: Fig 5-9 monitor, 5-10 pin config, 5-11 FETs, 5-12 interface.

## Links

- Product: https://www.ti.com/product/BQ76952
- EVM: https://www.ti.com/tool/BQ76952EVM
- Datasheet: https://www.ti.com/lit/ds/symlink/bq76952.pdf
- EVM UG: https://www.ti.com/lit/ug/sluuc33a/sluuc33a.pdf
- TIDA-010208: https://www.ti.com/lit/ug/tiduey5/tiduey5.pdf
