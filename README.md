# QFBMS

Work in progress: a 32-series battery-management PCB for Fungineers, using two BQ76952 monitors and an ESP32-C3-MINI-1. The circuit and routing are incomplete; this is not a manufacturing release.

## Open the design

Open `qfbms32.kicad_pro` in KiCad 10. The PCB, schematic, custom footprints (`qfbms.pretty/`), footprint table, and local 3D models (`3dmodels/`) are kept together. The PCB pad nets are the current working copy; the schematic is not an authoritative completed circuit.

## Editing rules

See [DESIGN_RULES.md](DESIGN_RULES.md). This repository split changes organization only: the project, board, and schematic files are byte-for-byte unchanged. Do not run old board-generation or scratch scripts against the working board.

## Current status

The dated notes in `docs/history/` capture earlier observations and proposed routing. They are historical, not validated instructions. In particular, the older topology document prescribes back-side filter capacitors while the later prompt requires front-side placement. The current placement policy is in DESIGN_RULES.md; no capacitor relocation or electrical correction was performed during migration.

Read the actual PCB for current connectivity. The progress dashboard is a connectivity aid, not electrical sign-off. Its current readout is saved in `docs/connectivity-snapshot.json`.

## Local tools

From this repository root:

```powershell
python -m pip install -r requirements.txt
python _tools/progress_dashboard/server.py
# http://localhost:5181
python _tools/pcb_dashboard/server.py
# http://localhost:5180
```

Run the two servers in separate terminals. Stop older copies using those ports first. The tools currently expect KiCad 10 at `C:\Program Files\KiCad\10.0`; scripts importing `pcbnew` use KiCad's bundled Python. Board Boxes includes the locally edited dashboard copied during migration.

## References and outputs

- `_reference/user_photos/`: placement photographs; IMG_2151 is the back.
- `_reference/vfbms32_wiring_32s_best.jpg`: harness reference.
- `_reference/ti_bq76952/`: vendor datasheet and evaluation-board material.
- `_reference/pinouts/`: preserved AGM pinout research.
- `_reference/firmware/`: reference firmware for a different, charge-only VBMS32 board; not QFBMS firmware.
- `docs/history/`: original topology, inventory, README and finish prompt, retained for traceability.
- `exports/`: regenerated previews and reports; ignored by Git.

The full pre-cleanup folder, experiments, backups and old exports are preserved locally in the source repository under `_migration_archive/qfbms-2026-11-02/`. They are not part of this repository. See [docs/MIGRATION.md](docs/MIGRATION.md).
