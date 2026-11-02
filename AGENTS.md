# Working on QFBMS

Read [README.md](README.md), [PLAN.md](PLAN.md), and [DESIGN_RULES.md](DESIGN_RULES.md) before design work. PLAN.md is the current build plan.

- Build a 32s charge-only BMS; discharge protection is outside scope.
- Preserve the placed connectors and balance/heatsink-related parts. Keep the BQ monitors approximately in their current regions, with the local flexibility described in DESIGN_RULES.md.
- Use the supplied VBMS32 firmware and Micro package as the intended software baseline. Read [docs/FIRMWARE_INTERFACE.md](docs/FIRMWARE_INTERFACE.md) before deciding pin assignments or charging behavior.
- Apply TI's electrical requirements to the actual stacked-monitor circuit and verify the implementation against the software.
- Treat docs/history/ as superseded reference material. Do not follow its discharge-switching instructions, blanket placement locks, or unverified pin maps.
- Keep documentation work separate from board, schematic, and firmware changes. Never run an old generator or import an unverified netlist over the working PCB.
