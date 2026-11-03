# Charge-only schematic draft

Functional draft: [open KiCad sheet](../qfbms32-charge-only-draft.kicad_sch). This sheet specifies functional connections; it contains no electrically connected symbols or routable netlist yet. Existing schematic and PCB are unchanged.

## Intended connections

- BQ1: SDA GPIO21 / SCL GPIO20. BQ2 connects through upper-domain interface.

- Each cell tap: verified input filter -> VC input; differential capacitors in local domain.

- Balancing: host commands both BQs. Preserve R_B row; external balance topology unresolved.

- BQ1 temperature inputs: TS1 / TS3 / ALERT / DCHG; HDQ = MOS temperature.

- BQ1 SRP/SRN: Kelvin charge-shunt sense. Verify resistance and complete software scaling.

- Charge ADC: channel 0; output ADC: channel 1. Verify divider rating and ratio.

- OPEN: H2440 pinout, Q1/Q2 roles, module pad map, upper interface, supply parts, balance circuit.

- Fixed connectors and heatsink components stay. PCB has not been changed.

## Next implementation pass

Replace the original bare-chip ESP32 symbol with a verified MINI-1 module symbol. Establish the charge-driver pinout and upper-monitor interface, then implement actual symbols, supporting passives and wires. Preserve existing PCB associations deliberately. Check electrical rules and render the resulting sheets before treating them as a circuit draft.
