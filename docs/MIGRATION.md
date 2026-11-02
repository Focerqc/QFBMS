# Repository split — 2026-11-02

Extracted from Focerqc/Fungineers-PCB-designs. The new repository contains QFBMS and its two local dashboards only. Shared dashboard edits were copied without altering the source tools. Unrelated boards were not changed.

The full original QFBMS folder is preserved in the source checkout at `_migration_archive/qfbms-2026-11-02/original-qfbms/`. Removed files are also grouped under `removed/`. This archive is local and excluded from Git. The old repository retains its committed history.

408 top-level scratch Python scripts, diagnostic dumps, backups, legacy generators and old renders/reports were removed from the active folder. Useful pinout PDFs, images and HTML were promoted to `_reference/pinouts/`. Old instructions and inventories are retained under `docs/history/` with historical labels.

No electrical changes were made. SHA-256 hashes of the original project, PCB and schematic are in `migration-core-hashes.json`. Dashboard paths and the board-box reference path were adjusted for a standalone repository root. No project-wide license was inferred or added; third-party reference notices remain with their sources.
