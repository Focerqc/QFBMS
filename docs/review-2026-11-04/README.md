# Review instructions for Grok and Gemini

Source checkpoint f056722b5af52c7b604633354ede1dbadf246c85, branch feature/bq-monitors, initially clean and tracking its published checkpoint. Generator was first run after extracting baseline.xml. Schematic/generator commit 27830c81b2c0da9590a3134f1f3a57a2a61b11c1. KiCad CLI 10.0.6 on Windows. The main schematic was only exported. The draft does not provide a live lower bus or either TS2 actuator.

Read [electrical decisions and bench criteria](electrical-review.md), [connectivity changes](netlist-comparison.md), and [main reconciliation](main-reconciliation.md). Open the root project and its three child sheets together. [Reviewed plot](monitor.pdf) is the plot of this hardware commit; the older PDF elsewhere in this repository is not this review.

## Reproduction

Run the baseline command from a clean copy of the source checkpoint, before regeneration. Create the output directory first. At the new revision run the remaining commands from the repository root. The comparison requires Python 3 and no external packages.

```powershell
$d = 'docs/review-2026-11-04'
$k = 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
& $k version
& $k sch export netlist --format kicadxml -o "$d/baseline.xml" qfbms32-bq-monitors.kicad_sch
& $k sch erc --format json -o "$d/baseline-erc.json" qfbms32-bq-monitors.kicad_sch
# At the schematic revision
python _tools/gen_bq_monitor_sheets.py
& $k sch export netlist --format kicadxml -o "$d/monitor.xml" qfbms32-bq-monitors.kicad_sch
& $k sch export netlist --format kicadxml -o "$d/main.xml" qfbms32.kicad_sch
& $k sch erc --format json -o "$d/erc.json" qfbms32-bq-monitors.kicad_sch
& $k sch export pdf -o "$d/monitor.pdf" qfbms32-bq-monitors.kicad_sch
python "$d/compare.py"
python _tools/check_bq_bus_admission.py
```

Original untouched baseline XML SHA-256 **308933e2a311d91c9c3acf53b2eeee1b453f128abf27a08b85f23ed53a961c50**. See SHA256SUMS for the actual review exports. New KiCad exports can embed local paths/dates; compare connectivity by pin sets. The XML exporter reported schematic annotation issues on the monitor draft at both revisions. References include legacy nonnumeric endings. Pin checks validate exported component uniqueness, not future board annotation. CLI reported HKCU registry access denied in the sandbox but produced complete, parseable output. ERC ran with the project settings, without added exclusions.

## Verification outcomes

- The complete component and pin inventories are identical. No new singleton or missing pin. Two four-member host nets each split in two. The lower REG1 label changed to REG1_BQ1 without changing its pin set. Two new explicit no-connect crosses on the root sheet mark the lower SDA/SCL sheet ports. No-connect crosses remain on both TS2 ports; these deliberately denote an open external connection. The XML listing identifies every singleton and NC-typed device pin. There are 30 harness-facing singletons at cells 1–15 and 17–31, external endpoints in this separate project.
- ERC: 0 errors, 43 warnings before and after, with identical item descriptions. All 30 isolated-label warnings are those cell taps. Eight pin-to-pin warnings are bidirectional unused functions tied to flagged local VSS (lower pins 29,30,32; upper 28–32). Confirm pin configuration before integration, especially upper analog functions initialized by common firmware. Five library warnings concern the embedded custom qfbms symbols and the unregistered external symbol library. The editor can render the embedded definitions. [All ERC items and coordinates](erc.json)
- Visually inspected all four rendered PDF pages. Page 1 shows the lower boundary open and the upper path connected. Pages 2–3 show distinct local TS2 and regulation nets; upper SRP/SRN terminate locally. Page 4 shows both controlled U204 paths, upper ISO and pull-up/bypass locations. No new clipped callouts. The separate monitor project omits the cell harness.
- Firmware guard model passed failed/retried lower verification, successful startup and repeated package GPIO9 gating. This model is not a hardware observation. The generated main reconciliation compares actual main XML against both monitor pin inventories, showing exact peers even when references or cell filter naming differ. Matching membership of an NC singleton is not proof that installed parts match.
- No oscilloscope, thermal, hot-leakage or assembled-pack test has been performed for this revision.
