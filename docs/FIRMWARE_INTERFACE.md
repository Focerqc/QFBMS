# Firmware interface and compatibility baseline

QFBMS is intended to be a 32-series, charge-only BMS with two BQ76952 monitors and an ESP32-C3-MINI-1. The software target is VBMS32-target VESC Express firmware plus the VBMS32 Micro package. Discharge protection is not a QFBMS design goal.

The supplied files in [`_reference/firmware/`](../_reference/firmware/) define the intended compatibility baseline. The assignments below describe that source; they do not establish that the current QFBMS PCB is already wired accordingly. See [PLAN.md](../PLAN.md) for implementation order and [DESIGN_RULES.md](../DESIGN_RULES.md) for placement constraints.

## What runs where

- The ESP32 runs the compiled firmware and the package's LispBM application, [`vbms32_micro.lisp`](../_reference/firmware/vbms32_micro.lisp). The Lisp application supplies charging, balancing, sleep, status and configuration behavior.
- Compiled C extensions in [`hw_vbms32.c`](../_reference/firmware/hw_vbms32.c) expose BQ communication, sensing, balance commands and GPIO switching to LispBM; registration starts at line 1311.
- The BQ76952 devices provide cell measurements and balancing commanded over I2C. Charge-switch control goes through ESP32 GPIO and the board's switching circuit; it is not implemented solely by BQ automatic protection settings.
- [`ui.qml.in`](../_reference/firmware/ui.qml.in) is the package's VESC Tool UI source. The [Makefile](../_reference/firmware/Makefile) generates `ui.qml`, and [`pkgdesc.qml`](../_reference/firmware/pkgdesc.qml) includes it alongside the Lisp application.

## ESP32 signal assignments

[`hw_vbms32.h`](../_reference/firmware/hw_vbms32.h), lines 44–45, selects hardware name `VBMS32` and target `esp32c3`. Lines 200–215 define:

- I2C: SDA GPIO21, SCL GPIO20.
- CAN: TX GPIO7, RX GPIO6.
- Enable/button input: `PIN_ENABLE`, GPIO2.
- Output-switch control: `PIN_OUT_EN`, GPIO4.
- Charge-switch control: `PIN_CHG_EN`, GPIO5.
- Precharge control: `PIN_PCHG_EN`, GPIO8.
- Communication enable: `PIN_COM_EN`, GPIO9.
- Power-switch enable: `PIN_PSW_EN`, GPIO10.
- Charge-voltage ADC: `ADC1_CHANNEL_0`; output-voltage ADC: `ADC1_CHANNEL_1`.

The Lisp application also starts buzzer PWM on GPIO3 in `main`. Some package code writes GPIO9 directly, so changing only the C header would not update every use of that signal.

The C charge/output/precharge extensions first assert `PIN_PSW_EN`, then set their respective control pin to the requested state (lines 795–813). Initial C setup drives all four switching outputs low and `PIN_COM_EN` high (lines 1377–1401). These are firmware signal levels; the physical gate-driver behavior must follow the actual circuit.

## Two-monitor startup and sensing

The C driver uses 100 kHz I2C and two final 7-bit addresses: `0x10` for BQ1 and `0x08` for BQ2 (`hw_vbms32.c`, lines 34–36). Startup at lines 475–518:

1. Drives `PIN_COM_EN` high to disable the other communication path while configuring the first BQ.
2. Initializes the first BQ at `0x08`, writes `0x20` to its I2C-address configuration, and applies the communication-mode change so the host addresses it at `0x10`.
3. Drives `PIN_COM_EN` low, then initializes the second BQ at `0x08` when its configured cell count is nonzero.

The compatible circuit therefore needs the communication gating assumed by this sequence. These addresses and GPIO controls alone do not define the physical interface between the two stacked voltage domains.

Cell reads use each device's configured cell count. Balance commands write the corresponding BQ's `CB_ACTIVE_CELLS` mask (`hw_vbms32.c`, lines 608–635 and 816–847).

Temperature initialization configures TS1, TS3, ALERT, DCHG and HDQ as ADC inputs with an 18 kΩ pull-up (`hw_vbms32.c`, lines 415–420). The temperature conversion at lines 638–724 assumes a 10 kΩ NTC, beta 3380, and the source's 500 Ω series-resistance correction.

The returned temperature list is: BQ1 internal, BQ1 TS1, TS3, ALERT, DCHG, HDQ, then BQ2 internal. In [`vbms32_micro.lisp`](../_reference/firmware/vbms32_micro.lisp), lines 257–299, `temp_num` selects zero to four of TS1/TS3/ALERT/DCHG as cell sensors, HDQ is the MOSFET temperature, and BQ1 internal temperature supplies `t-ic`. With zero cell sensors selected, that function substitutes 24 °C for the cell-temperature range.

## Current and voltage scaling

[`hw_vbms32.h`](../_reference/firmware/hw_vbms32.h), lines 218–222, declares a nominal 0.0002 Ω (0.2 mΩ) shunt and 220 kΩ / 4.7 kΩ divider scaling for both charge and output voltage. The C initialization derives BQ current gain from that shunt value (`hw_vbms32.c`, lines 435–441).

The C current extension reads BQ1 current and applies the PCB-version-dependent sign at lines 735–751. The Lisp helper then multiplies `bms-get-current` by **−0.2** (`vbms32_micro.lisp`, line 85). The charge loop treats negative application current as charging.

These are combined source assumptions, not an instruction to reproduce the multiplier blindly. Match the actual shunt network, sense polarity and divider values to the complete measurement path before treating reported current, voltage or cutoff thresholds as calibrated QFBMS measurements.

## Charging and balancing behavior

The supplied package already implements charging protection. Its main charge loop (`vbms32_micro.lisp`, lines 641–688) checks maximum cell voltage with separate start/end thresholds, minimum cell voltage, minimum/maximum cell temperature, MOSFET temperature and the charge-allow flag. Overcurrent while charging latches a charge fault; disconnecting the charger for five seconds clears that fault. Charger presence and minimum charge current also determine whether charging remains enabled.

The balancing loop (lines 747–815) applies minimum cell voltage, maximum current, cell temperature and BQ1 internal-temperature limits. It selects cells using voltage-difference start/end hysteresis, excludes adjacent selected cells and limits the number of simultaneous channels. Commands reach the BQs through the compiled extensions.

The C initialization sets automatic protection groups A and B to zero and selects host-controlled balancing (`hw_vbms32.c`, lines 428–433). That describes the division of work in this baseline; it does not mean the package lacks charging protection. Reuse requires the Lisp package as well as its matching compiled firmware.

## Versions and configuration

The supplied package [version file](../_reference/firmware/version) is **1.0.4**. The Lisp compatibility check requires firmware API **6** (`vbms32_micro.lisp`, line 867), and the supplied C extension returns **6** (`hw_vbms32.c`, lines 1305–1309).

The package descriptor accepts hardware name `VBMS32`, hardware type `custom module`, and firmware name `micro` or empty. The Lisp application sets the firmware name to `micro`. These checks are software compatibility checks, not verification of PCB wiring.

[`vbms32_conf_default.h`](../_reference/firmware/vbms32_conf_default.h) supplies compile-time defaults; [`vbms32_confparser.c`](../_reference/firmware/vbms32_confparser.c), from line 153, copies them into configuration. Examples in this source are:

- 16 cells on each BQ, one external cell-temperature sensor, and at most five balancing channels.
- Charge start/end maximum-cell thresholds of 4.16 V / 4.21 V; minimum cell voltage 2 V.
- Charge cell-temperature limits of 0–45 °C and MOSFET limit 85 °C.
- Maximum charge current 16 A, minimum charge current 0.5 A, and charger detection above 5 V.
- Balance voltage differences of 15 mV to start and 8 mV to stop, minimum cell voltage 3.5 V, maximum current 1 A, cell-temperature limit 45 °C and BQ-temperature limit 85 °C.

These are documented source defaults, not selected QFBMS operating settings. The application reads runtime configuration through `bms-get-param`; the C extensions also expose configuration changes and storage. Actual settings, calibration and component ratings must be reconciled when implementing this baseline on QFBMS.
