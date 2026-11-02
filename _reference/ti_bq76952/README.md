# TI BQ76952 electrical references

Use TI documentation for the monitor's electrical requirements, pin functions, ratings, and layout guidance. Apply it to the 32s charge-only objective in [PLAN.md](../../PLAN.md), the mechanical constraints in [DESIGN_RULES.md](../../DESIGN_RULES.md), and the supplied [firmware/package interface](../../docs/FIRMWARE_INTERFACE.md).

## Local reference material

- [BQ76952 datasheet](bq76952_datasheet.pdf): device requirements, pinout, and application circuits.
- [BQ76952EVM user's guide](BQ76952EVM_users_guide_sluuc33a.pdf): schematics in section 5.4, BOM in section 5.2, and layout. Figures 5-9 through 5-12 cover the monitor, pin configuration, FETs, and interface.
- [TIDA-010208 design guide](TIDA-010208_design_guide_tiduey5.pdf): a 10s–16s reference with high-side FETs and auxiliary power.
- [SLUC687A.zip](SLUC687A.zip): EVM board files, also extracted in [SLUC687A/](SLUC687A/).

## Applying a 16s reference to this 32s board

The EVM and TIDA-010208 are references for one monitor domain, not a complete two-monitor QFBMS circuit. The upper BQ uses the midpoint of the pack as its local reference; its interface to the ESP32 needs appropriate isolation or level shifting.

[TI's stacked-BQ76952 guidance](https://www.ti.com/document-viewer/lit/html/SSZT191/GUID-D1DE75C4-D7DF-46D6-BABF-B322A3EC1A9B) illustrates an isolated upper-monitor I2C interface and additional wake/control considerations. Its protection-switch example does not add a discharge-protection requirement to QFBMS. Check each support circuit against the chosen charge-only architecture and the firmware's communication-enable startup sequence.

## Values and configuration

Choose and document the final values for the actual circuit. Do not copy a generic EVM BOM over the supplied software's sensing assumptions:

- Cell-input filtering and balancing topology must be checked together, including the mechanically fixed balance/heatsink parts.
- The supplied firmware configures BQ temperature inputs with internal 18 kΩ pull-ups. An EVM external-bias example is not an instruction to add a 10 kΩ resistor to those inputs.
- The C firmware's current conversion assumes a 0.2 mΩ shunt, and the package applies an additional −0.2 multiplier. Reconcile that complete conversion with actual resistance and sense polarity before choosing values or claiming compatibility.
- The package controls balancing and charging policy. Its charge switching uses an ESP32 control output; do not assume the EVM's BQ CHG/DSG gate connections are the intended QFBMS implementation.
- Verify local decoupling, supply filters, communication pull-ups, and ratings for each monitor domain. Preserve the fixed mechanical features while fitting necessary supporting circuitry.

## Vendor links

- [BQ76952 product page](https://www.ti.com/product/BQ76952)
- [BQ76952EVM](https://www.ti.com/tool/BQ76952EVM)
- [Current datasheet](https://www.ti.com/lit/ds/symlink/bq76952.pdf)
- [EVM user's guide](https://www.ti.com/lit/ug/sluuc33a/sluuc33a.pdf)
- [TIDA-010208 design guide](https://www.ti.com/lit/ug/tiduey5/tiduey5.pdf)
