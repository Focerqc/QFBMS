# QFBMS — 32s charge-only BMS

QFBMS is a 32-series, charge-only battery-management board for a Fungineers pack. It uses two BQ76952 monitors and an ESP32-C3-MINI-1. The intended software is the VBMS32-target VESC Express firmware plus the supplied VBMS32 Micro package.

The board monitors cells and temperature, measures charging current, controls charging, and balances cells. **Discharge protection is outside the build scope.**

The circuit and routing are incomplete. Firmware compatibility is a design target; the current PCB has not been verified against the supplied software or validated for manufacture.

## Start here

- [Build plan](PLAN.md): the current objective, work order, open decisions, and completion criteria.
- [Design rules](DESIGN_RULES.md): mechanical constraints and how to change the working design.
- [Firmware and package interface](docs/FIRMWARE_INTERFACE.md): behavior and hardware assumptions already defined by the supplied software.

These documents supersede the proposals in [docs/history](docs/history/README.md). The historical discharge-switching instructions and blanket prohibition on moving any component are not the current build plan.

## What stays in place

Keep the placed connectors and the balance/heatsink-related components in their existing locations. Preserve the R_B1–R_B33 row and its thermal arrangement. Keep the two BMS monitors in approximately their existing areas; modest local adjustment is acceptable when needed for a sound layout.

Supporting circuitry should follow TI's applicable electrical and layout guidance while fitting these constraints. The exact capacitor/resistor set belonging to the heatsink arrangement still needs to be identified against the photos. The existing C_F1–C_F32 back-side placement is a separate unresolved issue; see [Design rules](DESIGN_RULES.md).

## How the software controls the board

The package's LispBM program runs on the ESP32 inside VESC Express. It decides when charging and balancing are allowed. The board-specific C firmware supplies the hardware functions: reading the BQ monitors and commanding balancing over I2C, and controlling external charge-switch circuitry through ESP32 GPIOs.

The supplied package already implements charging voltage, temperature, and current limits, plus balancing rules. Use those definitions as the compatibility baseline. Review the physical circuit, sensing calibration, and startup wiring against them before routing. The BQ automatic-protection configuration alone does not describe the complete charging behavior.

TI supplies the electrical requirements for the monitors and their supporting circuits. A 32s design also needs the stacked-monitor communication and power-domain treatment described in [the reference notes](_reference/ti_bq76952/README.md).

## Open the design

Open `qfbms32.kicad_pro` in KiCad 10. Keep the PCB, schematic, custom footprints in `qfbms.pretty/`, footprint table, and local `3dmodels/` together.

The PCB pad nets are the current working copy. The schematic is incomplete and must be reconciled deliberately; do not overwrite the PCB with an unverified schematic netlist or an old generation script.

The saved [connectivity snapshot](docs/connectivity-snapshot.json) is a migration-era report, not a live status or electrical sign-off. Read the actual board for current connectivity. Dashboard criteria may still reflect older topology assumptions.

## Local tools

From this repository root, install the dashboard dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run each dashboard in its own terminal:

```powershell
python _tools/progress_dashboard/server.py
# http://localhost:5181
```

```powershell
python _tools/pcb_dashboard/server.py
# http://localhost:5180
```

Stop older copies using those ports first. The tools currently expect KiCad 10 at `C:\Program Files\KiCad\10.0`; scripts importing `pcbnew` use KiCad's bundled Python.

## References and history

- [_reference/firmware/](_reference/firmware/): supplied VBMS32 firmware and package source, retained as the compatibility baseline.
- [_reference/ti_bq76952/](_reference/ti_bq76952/README.md): datasheet, evaluation-board material, and links to stacked-monitor guidance.
- [_reference/user_photos/](_reference/user_photos/): placement photographs; IMG_2151 shows the back.
- [Harness drawing](_reference/vfbms32_wiring_32s_best.jpg): external wiring reference; verify its connector pin mapping against the PCB.
- [_reference/pinouts/](_reference/pinouts/): preserved component pinout research.
- [docs/history/](docs/history/README.md): superseded topology, inventory, and finish instructions, retained for traceability.
- [exports/](exports/README.md): regenerated previews and reports, ignored by Git.

The original folder, experiments, and backups remain in the local source repository's migration archive. See [Migration history](docs/MIGRATION.md).
