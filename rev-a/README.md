# QFBMS rev A

A fresh, generated attempt at the 32s charge-only BMS. It keeps the old board's outline,
connectors and R_B1–R_B33 row, and the supplied VBMS32 firmware. Everything else was redrawn
from the datasheets.

**Status (2026-11-17):** complete schematic, every part has a stated purpose, placed and
routed on 4 layers with shaped charge-path pours. **Not ready to order:** 4 connections are still
open and 7 small DRC items remain (list below), and the design assumes a conformal-coated board.
Work stopped here on purpose: rev A is a reference model, not a build commitment. Rev A is a guess-and-check
build. An outside review (below) found one critical circuit error and several major ones, so
**as drawn it would not work safely**. They are recorded, not fixed: the PCB is left as is.

| Check | Result |
|---|---|
| Parts | 193, each with a `Purpose` field (schematic property, footprint field and [bom.csv](bom.csv)) |
| Netlist vs. circuit table | 562 pins checked by kicad-cli, 0 mismatches, 0 single-pin nets |
| ERC | 0 errors, 1 expected warning (isolator GND2 sits on CELL16) |
| Fixed parts | 45 checked (connectors + R_B1–R_B33): position, rotation, side, every pad identical to `qfbms32.kicad_pcb` |
| Placement | 193/193 on the front, each inside its voltage domain (upper monitor between x 41 and 63) |
| Routing | Freerouting, 4 layers, In1 = GND / CELL16 reference planes |
| PCB DRC (coated rules) | Schematic parity 0, **4 unconnected**, 7 small errors (2 GND tracks too near the edge, 4 starved thermal reliefs, 1 dangling stub). Also 3 pin-to-pin pairs set by TI's pinouts and 6 items in the fixed parts' own footprints (see `route/drc-summary.json`) |
| PCB DRC (uncoated, 0.6 mm by voltage bank) | ~280 clearance hits: not met. Use conformal coating or re-route by hand |

## Files

| Path | What |
|---|---|
| `tools/circuit.py` | **The design.** Every part, pin→net map, value, MPN and purpose |
| `tools/gen_schematic.py` | Writes `qfbms-rev-a.kicad_sch`, `bom.csv`, the local symbol lib and lib tables |
| `tools/check_schematic.py` | kicad-cli netlist parity against `circuit.py`, plus ERC |
| `tools/build_board.py` | Writes `qfbms-rev-a.kicad_pcb` from the old board's outline and fixed parts (old file only read) and places every part by connectivity inside its voltage domain |
| `tools/set_rules.py` | Net classes (Default / POWER / HV / CHARGE) and `.kicad_dru`. `--uncoated` writes the 0.6 mm voltage-bank rules |
| `tools/route_board.py` | `export` adds the In1 planes and writes `route/*.dsn`; `import` reads Freerouting's `.ses` |
| `tools/check_board.py` | DRC + parity, sorted into real problems, chip-pinout pairs and fixed-footprint items |
| `qfbms_reva.pretty/`, `qfbms_reva.kicad_sym` | XT30, USB-C, ESP32, buzzer footprints (copied); ESP32-C3-MINI-1 and VOM1271 symbols |
| `render/` | Board render and schematic PDF |

Regenerate (KiCad 10; `KPY` = `"C:\Program Files\KiCad\10.0\bin\python.exe"`):

```
python tools/gen_schematic.py && python tools/check_schematic.py
python tools/set_rules.py
KPY tools/build_board.py
KPY tools/route_board.py export
java -jar freerouting-2.0.1.jar -de route/qfbms-rev-a.dsn -do route/qfbms-rev-a.ses -mp 100 -mt 1 -da
KPY tools/route_board.py import --no-pours
python tools/check_board.py
```

Freerouting 2.0.1 needs Java 21. Headless mode (`--gui.enabled=false`) exits without saving.
With the window it routes, saves, shows a settings pop-up and closes itself. Its settings file
(`%TEMP%\freerouting\freerouting.json`) enables telemetry by default; it was switched off here.
`route/placed-planes.kicad_pcb` is the placed, unrouted board the current route came from.

Change the design in `circuit.py` only. The schematic is label-per-pin and is never edited by hand.

## How it works

- **Monitors.** Two BQ7695202 (I2C with CRC, REG1 on at 3.3 V: what the firmware expects).
  U_BQ1 does cells 1–16 against GND. U_BQ2 does cells 17–32 against CELL16. Each has TI's
  typical supply: a BAT diode with RC, a BCX56-16 (80 V, SOT-89) REG0 preregulator with its own collector
  diode, a 10 MΩ BREG resistor, 22 nF on REGIN, 2.2 µF on REG18, 1 µF on REG1, and 2.2 µF from CP1 to BAT.
- **Cell inputs.** R_B1–R_B33 (27 Ω, fixed row) are the cell input resistors, one per tap.
  Tap 16 is shared by both monitors. 32 × 100 nF differential capacitors. Internal balancing ≈ 50 mA.
- **Always awake.** A 10 kΩ from TS2 to VSS wakes each monitor from SHUTDOWN (TI's note on
  thermistors at TS2). The firmware only uses DEEPSLEEP, so no wake circuit is needed.
  PACK has 10 kΩ to its own top of stack and LD goes to VSS (TI: no high-side FETs).
- **Current.** One 1 mΩ shunt between BAT− and charger negative, Kelvin-tied with net ties,
  100 Ω/100 nF filter. The Micro package scales the firmware's 0.2 mΩ gain by −0.2, so 1 mΩ
  with SRP on the battery side is what it expects (PCB_VERSION 2). No firmware change needed.
- **Temperatures.** J_T1–J_T4 go to TS1, TS3, ALERT and DCHG. RT1, beside the FETs, goes to HDQ.
  Each has a 499 Ω series resistor (the firmware subtracts 500 Ω), with a 10 k B3380 NTC.
- **Charge switch.** Q1 and Q2 are back-to-back 200 V N-FETs (TOLL), so the charge port is dead
  either way when off. A VOM1271 photovoltaic driver makes the floating ~8 V gate drive with
  no high-side supply. Its LED needs both CHG_EN (GPIO5) **and** PSW_EN (GPIO10), matching the
  firmware's order.
- **Upper-monitor link.** The host I2C bus goes through two 74CBTLV1G125 bus switches to an
  ISO1640. COM_EN (GPIO9) high opens the switches, so the firmware can re-address U_BQ1
  while U_BQ2 is hidden. The isolator's upper side runs from U_BQ2's REG1 through a PFET.
  An opto turns that PFET on only while COM_EN is low, so the isolator doesn't drain cells
  17–32 in sleep.
- **Power.** LTC7138 (140 V) from the fused pack through a 100 Ω/2 µF filter, to 5.0 V. It is
  diode-ORed with USB VBUS, then an AP2112K makes 3.3 V. The ESP32 can be flashed over USB
  without the pack.
- **ESP32-C3-MINI-1.** Pins exactly as `hw_vbms32.h`. GPIO2 (ENABLE) idles low with a wake
  button to 3.3 V, because the firmware treats high as "stay awake". GPIO8/GPIO9 straps are
  pulled high. 2.2 MΩ/47 kΩ dividers keep the firmware's 220k/4.7k ratio at 1/10 the drain.
- **CAN.** ISO1050 isolated, side 2 powered from the VESC's 5 V on J_COMM1, with an optional
  120 Ω termination behind solder jumper JP1.

## Removed from the old board, and why

| Old parts | Why they are gone |
|---|---|
| R_F1–R_F32 (20 Ω) | Second series row. R_B1–R_B33 already are the cell input resistors |
| R_SH2 | Second shunt. One 1 mΩ matches the firmware scaling |
| U_SSR1 "GSRELAY", C_SSR1/2, R_SSR1/2 | Unidentified relay/driver. Replaced by the VOM1271 |
| D_BST1, D_PRI1–3, D_SEC1–3, R_SEC1, FB1, C_TAN1, C_FLT1, C_DISC | Old boost/isolated-supply gate-drive attempt. The photovoltaic driver needs none of it |
| D_CHG1–3 (DSK320), R_CHG1/2, R_DSG1, R_S1/2, R_G1, R_GS1, D_GS1, D_S1 | Old charge/discharge-path parts. Discharge is out of scope; the new charge path is Q1/Q2, R1, D1 |
| EP pad on U_BQ1/U_BQ2 footprints | The BQ76952 TQFP-48 has no exposed pad |

U4 (LTC7138), U7 (ISO1050), Q1, F1, BZ1, the C_F caps and U_BQ1/U_BQ2 keep their references
with new circuits.

## External review (2026-11-17, recorded, not fixed)

A ChatGPT review of `circuit.py`, the README, the BOM, the firmware and the PCB. Its local
copies were used; it could not open the public links. The top finding was checked against
`circuit.py` and is correct. Decision: leave the PCB as is and record everything here.

### Hardware (rev A design errors)

| Severity | Part / net | Finding | Fix if rev B happens |
|---|---|---|---|
| **Critical** | R_B17, TAP16_F, upper VC0 | Lower VC16 and upper VC0 share TAP16_F through R_B17, but upper VSS is the unfiltered CELL16. Balancing cell 16 (~50 mA × 27 Ω) puts upper VC0 about **1.35 V below its VSS**; SLUSE13B §7.1 allows −0.3 V. Normal operation, not a fault. | Give upper VC0 its own resistor from CELL16 and a local VC0–VSS capacitor; move C_F17's lower end to that node. |
| Major | Lower VC0, CELL0, GND | CELL0 is not tied to VSS/GND on the PCB, so VC0's reference depends on the harness. TI §16.3 needs VC0 tied to VSS through its resistor on the board before cells attach. Neither monitor has the VC0–VSS capacitor (Table 16-3). Plug-in-any-order tolerance must not be claimed. | Add the local VC0 reference and capacitor; engineer the CELL0 / main-negative link so a missing main lead can't push current through a sense wire. |
| Major | R112–R116 | The 499 Ω series resistors double-count: the firmware's 500 Ω correction is for the chip's own ~526 Ω pad resistance (§7.23). A real 45 °C reads about 42 °C. | Remove them, or change the conversion to subtract both. |
| Major | NT1, NT2, R_SH1 | The net ties are not at the shunt pads (NT1 ~8 mm, NT2 ~21 mm away), so the "Kelvin" sense shares charge-current copper. With a 1 mΩ shunt that shifts the calibration. | Start each sense trace at its shunt pad with the net tie there; re-check the current gain. |
| Major | R9 | A plain 100 Ω 1206 takes the hot-plug inrush: about 18 mJ, 181 W peak, τ 200 µs, repeated with connector bounce. | Use a pulse-rated part or a proper inrush network. |
| Major (unqualified) | U5, R1, Q1, Q2 | The VOM1271's 7.8–8.4 V is open-circuit; minimum short-circuit current is 6 µA at 10 mA LED current. R1 alone takes 8 µA at 8 V. The loaded gate voltage is not guaranteed, so "fully on at 7.8 V" isn't a valid design condition. | Work out minimum loaded V_GS over temperature, pick the FET for it, and check turn-on SOA; change the driver or bias if needed. |
| Correction | U4 | 140 V is the LTC7138's **absolute maximum**, not only its operating limit. 134.4 V at full charge is 5.6 V under it. | Re-evaluate the supply topology or add real input transient protection. |

### Firmware (inherited from VBMS32, not changed here)

| Severity | Area | Finding |
|---|---|---|
| **Critical** | Charge enable on comms failure | On a persistent BQ comms failure, recovery runs `init-hw` (unbounded retries) before `bms-set-chg 0`, so GPIO5/10 can keep the charge FETs on indefinitely. Automatic BQ protections are disabled, and the board has no independent interlock. Fix: force charge off before any recovery, and add a hardware watchdog that can cut the VOM1271 LED. |
| Major | FET thermistor fault | An invalid HDQ reading becomes −1 °C, which passes the "below max" charge check, so an open sensor doesn't stop charging. |
| Major | Upper admission | The upper monitor is connected even if moving the lower one to 0x10 failed: address collision. |
| Major | COM_EN settling | `with-com` turns on the bus switches and the isolator's upper supply and reads immediately. ISO1640 needs up to 151 µs UVLO recovery plus the supply ramp. The C startup already waits 50 ticks; the Lisp path doesn't. |

### Reviewed and found correct

BQ pin numbering and unused-pin terminations, PACK/LD hookup, upper reference on CELL16, BAT and
collector diodes, BREG resistor, current sign and the −0.2 scaling (5 A charging reads −5 A),
the common-source FET topology (VOM1271 has active turn-off), the LTC7138 pinout, ANODE diode,
adjustable mode, divider and inductor.

### Still unverified

Sleep current and the upper-only isolator drain while comms stay on (TS2's 10 kΩ also prevents
long-term SHUTDOWN, as TI warns); charger hot-plug gate behaviour; a missing CELL16 or other
open taps; insulation beyond the coated-rules DRC; copper current and thermal; ADC ranges;
component voltage and pulse derating.

## Check before ordering

1. **Finish 4 connections by hand** (`route/drc-summary.json`): R1 pad 2 to the CHG_SRC pour,
   U_BQ1 pin 17 (GND) to the plane, D2 pad 1 to the SW track. Also move the two GND tracks off the
   board edge, delete one dangling CHG_NEG stub on In2, and fix 4 starved thermal reliefs.
   `tools/maze_route.py` (a small grid router) closed the rest; it can be re-run on what is left.
2. **Buck layout** is done by hand: C3/C4 sit under U4 with D2 beside them.
3. **High-voltage spacing.** The coated rules pass. Uncoated IPC-2221B B2 spacing (0.6 mm
   between nets more than 30 V apart) fails in ~280 places. Specify conformal coating, or re-route those areas.
4. **Fixed-part DRC that existed before rev A:** J_CELL3/J_CELL4 and J_CELL4/J_COMM1 courtyards
   overlap, USB-C GND pads are close to its holes, and the XT30 tabs are close to the edge.
   Check them against the real connectors before changing anything.
5. **Part choices to confirm:** F1 has no part yet (needs ≥150 V DC SMD). Q1/Q2 must be fully on at 7.8 V
   gate (IPT111N20NFD is the candidate). The 180 µH inductor needs Isat ≥ 0.7 A.
   VOM1271 pin 4 is assumed to be + (meter it on the first unit).
6. **Margins:** the LTC7138 sees 134.4 V at full charge (140 V operating). No TVS can clamp
   that range usefully, so only the RC filter protects it. The FETs and diodes are 200 V.
7. **Harness:** the cell plug pin order is the old board's assignment. Confirm it against
   `_reference/vfbms32_wiring_32s_best.jpg` and by continuity. Plug BAT− first, then J_CELL1→J_CELL4.
8. **Bench order:** power from a current-limited supply on J_BAT1 (≥40 V) → flash over USB →
   check both BQ addresses → cells on a simulator → charge FET drive → then a real pack.
9. **Firmware assumptions to watch:** the isolator's upper side powers up when COM_EN goes
   low, and `with-com` retries 4 times. If U_BQ2 reads fail intermittently, add a short delay
   after `gpio-write 9 0`.
