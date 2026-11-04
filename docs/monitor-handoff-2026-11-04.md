# Monitor handoff · 2026-11-04

This checkpoint preserves the working draft for the next agent. The parent revision before checkpointing was `7fcd2bc`. Existing edits span the maintained generator, four monitor sheets, the firmware adaptation, dashboard tools and box metadata. The saved monitor PDF predates this handoff. No regeneration, electrical validation, ERC or PDF review was performed for this checkpoint.

Read the [electrical decision note](monitor-electrical-decisions-2026-11-03.md) and [firmware interface](FIRMWARE_INTERFACE.md) alongside the root project instructions. Start from the checked-out monitor sheets and export their component-pin netlist before running `_tools/gen_bq_monitor_sheets.py`. Record the starting commit, dirty paths and KiCad version with the export.

Keep the existing GPIO9-controlled TMUX154E and upper ISO1640 admission sequence. Verify the lower address at 0x10 before connecting the upper device at 0x08. Keep upper SRP/SRN at CELL16. Read the checkpointed firmware as the baseline for the next task.

Resolve the lower powered-off I2C interface first. The second ISO1640B is a candidate. Check both directions of low-level propagation with the upper switch closed, including whether the two offset-low ports can recognize each other's asserted low. Record any unsupported power or ramp range. If no candidate meets the limits, leave a labeled OPEN interface.

Then evaluate local-VSS TS2 wake for each monitor with its REG1 off. Establish who powers the wake source, who drives it, and what releases TS2. Leave an explicit port dependency wherever the source, GPIO or timing cannot be justified.

Keep edits inside the separate monitor project and its maintained generator. Compare before/after nets as sets of reference-pin pairs and explicitly list singleton or unconnected pins. Report ERC findings, inspect every PDF page and reconcile the main schematic read-only. Keep the design charge-only. Main schematic, PCB, placement, routing and firmware are outside the next edit scope.
