# Board Boxes on GitHub Pages

The home page uses the actual local PCB dashboard interface: board viewing, layers, part inspection, box drawing, selection, undo/redo and Copy Prompt. **News** opens the previous project overview, corrected to RS50 cells.

The hosted dashboard loads published board data and renders. Annotations save in this browser, separately for each board; they do not update repository files or sync between devices. Copy Prompt exports placement instructions. Fresh KiCad render controls are disabled on the hosted page; generate renders locally before publishing.

## Refresh

Run `python _tools/pcb_dashboard/export_site.py` with KiCad 10 installed. It reads the working PCB and optional reconciliation snapshot without changing them, then copies the dashboard UI and selected reference assets. The generated app uses hosted.js for snapshot reads and browser saves. Verify with `node _tools/pcb_dashboard/check_hosted.cjs`.

Refresh schematic PDFs in files/ deliberately, including full-system-schematic.pdf (main schematic followed by the separate monitor project). Preserve draft labels and update files/snapshot.json source provenance when refreshing PDFs. These projects are not a reconciled system schematic.

Push site changes to main to publish through .github/workflows/pages.yml. Existing hosting and audience are unchanged. URL: https://focerqc.github.io/QFBMS/.
