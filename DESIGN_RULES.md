# QFBMS editing rules

The working board is `qfbms32.kicad_pcb`. Check placement against `_reference/user_photos/`; vendor reference designs supply pin functions and values, not permission to alter placement.

- Preserve footprint positions, rotations, packages and values. Route around placed parts. Identify the reference and pin when an existing part cannot perform a required function.
- The photographed back has no components. The existing C_F1–C_F32 placement is a known unresolved exception in the old notes. Front-side placement beside the corresponding monitor is the stated target, clear of packages and thermal pads; do not relocate these parts during maintenance or repository cleanup. Confirm the specific placement before electrical work.
- Do not add, replace or move other parts based on the old finish prompt. Do not treat an unnetted footprint as expendable. Keep R_B1–R_B33 in place.
- The PCB is the working source for pad nets. Do not overwrite it by running historical generators or importing an unverified schematic netlist.
- Historical proposals for pin assignments, FET connections, I2C, thermistor bias and gate drive require verification before implementation. The migration did not validate them.
- Report missing parts and uncertain pin functions explicitly. Connectivity counts and rendered previews do not establish electrical correctness.
