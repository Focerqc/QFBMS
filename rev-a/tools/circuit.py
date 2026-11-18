"""QFBMS rev A circuit, as data.

Every part has a block and a purpose. The schematic, BOM and board are generated
from this table; nothing is drawn by hand.

Pin maps come from the KiCad 10 library symbols (checked against TI, Espressif
and Vishay pin tables, see ../README.md). Each `pins` dict maps pin number -> net.
Pins listed in `nc` get a no-connect flag. Every symbol pin must be in one of the two.
"""

PARTS = []

FP_R0402 = "Resistor_SMD:R_0402_1005Metric"
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_R0805 = "Resistor_SMD:R_0805_2012Metric"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric"
FP_C0402 = "Capacitor_SMD:C_0402_1005Metric"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
FP_C1210 = "Capacitor_SMD:C_1210_3225Metric"
FP_SOD123 = "Diode_SMD:D_SOD-123"
FP_SMA = "Diode_SMD:D_SMA"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SOT223 = "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
FP_TOLL = "Package_TO_SOT_SMD:Infineon_PG-HSOF-8-1"
FP_SOP4 = "Package_SO:SOP-4_4.4x2.6mm_P1.27mm"


def part(ref, lib, value, fp, pins, purpose, block, nc=(), mpn="", fixed=False):
    PARTS.append(dict(ref=ref, lib=lib, value=value, fp=fp, pins=dict(pins),
                      nc=list(nc), purpose=purpose, block=block, mpn=mpn, fixed=fixed))


def R(ref, value, a, b, purpose, block, fp=FP_R0402, mpn=""):
    part(ref, "Device:R", value, fp, {"1": a, "2": b}, purpose, block, mpn=mpn)


def C(ref, value, a, b, purpose, block, fp=FP_C0402, mpn=""):
    part(ref, "Device:C", value, fp, {"1": a, "2": b}, purpose, block, mpn=mpn)


# ---------------------------------------------------------------- cell taps
# Connector pin order is the old board's verified pad assignment:
# J_CELL1 1..10 = CELL9..CELL0, J_CELL2 1..9 = CELL18..CELL10,
# J_CELL3 1..8 = CELL26..CELL19, J_CELL4 1..6 = CELL32..CELL27.
for ref, top, n, fp in [("J_CELL1", 9, 10, "Connector_JST:JST_GH_BM10B-GHS-TBT_1x10-1MP_P1.25mm_Vertical"),
                        ("J_CELL2", 18, 9, "Connector_JST:JST_GH_BM09B-GHS-TBT_1x09-1MP_P1.25mm_Vertical"),
                        ("J_CELL3", 26, 8, "Connector_JST:JST_GH_BM08B-GHS-TBT_1x08-1MP_P1.25mm_Vertical"),
                        ("J_CELL4", 32, 6, "Connector_JST:JST_GH_BM06B-GHS-TBT_1x06-1MP_P1.25mm_Vertical")]:
    part(ref, f"Connector_Generic:Conn_01x{n:02d}", f"CELL{top}-CELL{top - n + 1}", fp,
         {str(i + 1): f"CELL{top - i}" for i in range(n)},
         f"Balance-lead plug, taps CELL{top} down to CELL{top - n + 1} (fixed position)",
         "cells", fixed=True)

# R_B1..R_B33: the fixed row. R_B(33-k) carries tap k into the monitors (TI cell input
# resistor; internal balancing current also flows through it, ~50 mA with 27 ohm).
for k in range(33):
    ref = f"R_B{33 - k}"
    part(ref, "Device:R", "27R 0805", FP_R0805, {"1": f"CELL{k}", "2": f"TAP{k}_F"},
         f"Cell-input / balance resistor for tap {k} (fixed position)", "cells", fixed=True)

# Differential cell filter caps, VC(n) to VC(n-1), 32 of them (TI typical application)
for n in range(1, 33):
    C(f"C_F{n}", "100n 16V", f"TAP{n}_F", f"TAP{n - 1}_F",
      f"Cell {n} input filter (with R_B) for the {'lower' if n <= 16 else 'upper'} monitor",
      "cells")


# ---------------------------------------------------------------- monitors
def monitor(u, vss, top, base, tap0, upper):
    """One BQ7695202. `base` is the numeric start for its support refs."""
    r = lambda i: f"R{base + i}"
    c = lambda i: f"C{base + i}"
    d = lambda i: f"D{base + i}"
    p = {str(16 - i): f"TAP{tap0 + i}_F" for i in range(16)}  # VC0..VC15 = pins 16..1
    p["48"] = f"TAP{tap0 + 16}_F"                              # VC16
    p["17"] = vss
    tag = "BQ2" if upper else "BQ1"
    p.update({"24": f"REG18_{tag}", "35": f"REG1_{tag}", "36": f"REGIN_{tag}",
              "37": f"BREG_{tag}", "46": f"CP1_{tag}", "47": f"BAT_{tag}",
              "42": f"PACK_{tag}", "41": vss, "33": vss, "38": vss,
              "22": f"TS2_{tag}", "29": vss, "30": vss})
    if upper:
        p.update({"18": vss, "20": vss, "21": vss, "23": vss, "28": vss,
                  "25": f"ALERT_{tag}", "31": f"DCHG_{tag}", "32": f"DDSG_{tag}",
                  "26": "SCL_BQ2", "27": "SDA_BQ2"})
    else:
        p.update({"18": "SRP", "20": "SRN", "21": "TS1", "23": "TS3", "25": "ALERT_T3",
                  "31": "DCHG_T4", "28": "HDQ_TFET", "32": f"DDSG_{tag}",
                  "26": "SCL", "27": "SDA"})
    half = "cells 17-32" if upper else "cells 1-16"
    part(u, "Battery_Management:BQ76952PFB", "BQ7695202", "Package_QFP:TQFP-48_7x7mm_P0.5mm",
         p, f"{'Upper' if upper else 'Lower'} monitor, {half}: voltages, balancing"
         + ("" if upper else ", charge current, temperatures") +
         ". 02 variant = I2C+CRC, REG1 on at 3.3 V (firmware baseline)",
         "upper" if upper else "lower", nc=["19", "34", "39", "40", "43", "44", "45"],
         mpn="BQ7695202PFBR")
    blk = "upper" if upper else "lower"
    # Supply: BAT diode + RC, REG0 preregulator NPN with its own collector diode
    part(d(1), "Device:D", "BAV21W", FP_SOD123, {"2": top, "1": f"BATD_{tag}"},
         "BAT series diode: keeps the monitor alive through a stack dip (TI 16.2)", blk, mpn="BAV21W")
    R(r(1), "100R 0603", f"BATD_{tag}", f"BAT_{tag}",
      "Limits inrush into the BAT capacitor when the balance plugs go in", blk, fp=FP_R0603)
    C(c(1), "1u 100V", f"BAT_{tag}", vss, "BAT pin hold-up capacitor (TI 16.2)", blk, fp=FP_C0805)
    C(c(2), "2.2u 25V", f"CP1_{tag}", f"BAT_{tag}",
      "Charge-pump capacitor, CP1 to BAT (datasheet 9.3)", blk, fp=FP_C0603)
    part(d(2), "Device:D", "BAV21W", FP_SOD123, {"2": top, "1": f"COLL_{tag}"},
         "REG0 collector diode, blocks reverse current through BREG (TI 16.2.2)", blk, mpn="BAV21W")
    part(f"Q{base}", "Transistor_BJT:Q_NPN_BCE", "BCX56-16", "Package_TO_SOT_SMD:SOT-89-3",
         {"1": f"BREG_{tag}", "2": f"COLL_{tag}", "3": f"REGIN_{tag}"},
         "REG0 preregulator transistor, drops the <=67 V half-stack to ~5 V REGIN (80 V, SOT-89)",
         blk, mpn="BCX56-16")
    R(r(2), "10M", f"BREG_{tag}", vss, "BREG to VSS, prevents leakage turn-on (TI 16.2.2)", blk)
    C(c(3), "22n 25V", f"REGIN_{tag}", vss, "REGIN capacitor, 15-27 nF required (datasheet 7.5)", blk)
    C(c(4), "2.2u 10V", f"REG18_{tag}", vss, "REG18 decoupling, 1.8-22 uF (datasheet 7.5)", blk, fp=FP_C0603)
    C(c(5), "1u 10V", f"REG1_{tag}", vss, "REG1 output capacitor; REG1 is enabled by firmware", blk, fp=FP_C0603)
    R(r(3), "10k", f"PACK_{tag}", top,
      "PACK to top of stack via 10k, as TI says for designs without high-side FETs", blk)
    R(r(4), "10k", f"TS2_{tag}", vss,
      "TS2 to VSS: auto-wakes the monitor from SHUTDOWN and reads 25 C (TS2 is never configured)", blk)
    R(r(5), "10k", f"DDSG_{tag}", vss, "Defines DDSG (disabled by firmware) whatever its power-up default", blk)
    if upper:
        R(r(6), "10k", f"ALERT_{tag}", vss, "Defines unused ALERT; safe if it powers up as an output", blk)
        R(r(7), "10k", f"DCHG_{tag}", vss, "Defines unused DCHG; safe if it powers up as an output", blk)


monitor("U_BQ1", "GND", "CELL16", 100, 0, upper=False)
monitor("U_BQ2", "CELL16", "CELL32", 200, 16, upper=True)

# Lower-monitor current sense: one 1 mOhm shunt. The Micro package scales the
# firmware's 0.2 mOhm gain by -0.2, i.e. it expects 1 mOhm with charge = SRP > SRN.
part("R_SH1", "Device:R", "1m 2512 1%", "Resistor_SMD:R_2512_6332Metric",
     {"1": "GND", "2": "CHG_NEG"},
     "Charge-current shunt, battery side to charger negative. 1 mOhm matches the firmware scaling",
     "charge", mpn="1 mOhm 2512 metal strip, TCR <= 50 ppm")
part("NT1", "Device:NetTie_2", "NetTie", "NetTie:NetTie-2_SMD_Pad0.5mm",
     {"1": "GND", "2": "SENSE_P"}, "Kelvin pick-off at the shunt's battery-side pad", "lower")
part("NT2", "Device:NetTie_2", "NetTie", "NetTie:NetTie-2_SMD_Pad0.5mm",
     {"1": "CHG_NEG", "2": "SENSE_N"}, "Kelvin pick-off at the shunt's charger-side pad", "lower")
R("R110", "100R", "SENSE_P", "SRP", "SRP filter resistor (TI layout guidelines)", "lower")
R("R111", "100R", "SENSE_N", "SRN", "SRN filter resistor (TI layout guidelines)", "lower")
C("C110", "100n", "SRP", "SRN", "SRP-SRN differential filter (TI layout guidelines)", "lower")

# Temperatures: firmware reads TS1, TS3, ALERT, DCHG (cells) and HDQ (FETs) with an
# 18k pull-up, 10k B3380 NTC and a 500 ohm series correction -> 499R series parts.
for ref, conn, net, label in [("R112", "J_T1", "TS1", "T1"), ("R113", "J_T2", "TS3", "T2"),
                              ("R114", "J_T3", "ALERT_T3", "T3"), ("R115", "J_T4", "DCHG_T4", "T4")]:
    R(ref, "499R 1%", f"{label}_EXT", net,
      f"{label} series resistor: ESD for the off-board NTC; firmware subtracts 500 ohm", "lower")
    part(conn, "Connector_Generic:Conn_01x02", label,
         "Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical",
         {"1": f"{label}_EXT", "2": "GND"}, f"Cell thermistor {label} plug (fixed position)",
         "lower", fixed=True)
R("R116", "499R 1%", "TFET", "HDQ_TFET", "FET NTC series resistor (firmware 500 ohm correction)", "lower")
part("RT1", "Device:Thermistor_NTC", "10k B3380", FP_R0603, {"1": "TFET", "2": "GND"},
     "On-board NTC beside the charge FETs; firmware reads it as MOSFET temperature",
     "charge", mpn="NCP18XH103F03RB")


# ---------------------------------------------------------------- charge path
part("J_CHG1", "Connector_Generic:Conn_01x02", "XT30 charger", "qfbms_reva:XT30PW-F_Lugs",
     {"1": "CHG_POS", "2": "CHG_NEG"}, "Charger input (fixed position)", "charge", fixed=True)
part("J_BAT1", "Connector_Generic:Conn_01x02", "XT30 pack", "qfbms_reva:XT30PW-M_Lugs",
     {"1": "BAT_POS", "2": "GND"}, "Pack main leads; charge current returns through here (fixed position)",
     "charge", fixed=True)
part("F1", "Device:Fuse", "10A >=150VDC", "Fuse:Fuse_2920_7451Metric", {"1": "BAT_POS", "2": "PACK_F"},
     "Fuses everything on the board against the pack. PART OPEN: needs a >=150 V DC SMD rating",
     "charge", mpn="OPEN")
fet = "200V N-MOSFET TOLL, spec'd at <=8V gate"
part("Q1", "Transistor_FET:Q_NMOS_GSD", fet, FP_TOLL, {"1": "CHG_GATE", "2": "CHG_SRC", "3": "PACK_F"},
     "Pack-side charge FET; back-to-back with Q2 so nothing flows either way when off",
     "charge", mpn="e.g. IPT111N20NFD (confirm)")
part("Q2", "Transistor_FET:Q_NMOS_GSD", fet, FP_TOLL, {"1": "CHG_GATE", "2": "CHG_SRC", "3": "CHG_POS"},
     "Charger-side charge FET; keeps the charge port dead when charging is off",
     "charge", mpn="e.g. IPT111N20NFD (confirm)")
part("U5", "qfbms_reva:VOM1271", "VOM1271", FP_SOP4,
     {"1": "LED_A", "2": "LED_K", "4": "CHG_GATE", "3": "CHG_SRC"},
     "Photovoltaic gate driver: makes ~8 V floating gate drive, no high-side supply needed",
     "charge", mpn="VOM1271T")
R("R1", "1M", "CHG_GATE", "CHG_SRC", "Holds the FET gates off when the driver is dark", "charge")
part("D1", "Device:D_Zener", "12V", FP_SOD123, {"1": "CHG_GATE", "2": "CHG_SRC"},
     "Gate clamp, keeps transients under the FETs' +-20 V gate rating", "charge", mpn="BZT52C12")
R("R2", "120R", "3V3", "LED_A", "Sets ~15 mA through the VOM1271 LED", "charge")
part("Q3", "Transistor_FET:Q_NMOS_GSD", "AO3400A", FP_SOT23, {"1": "CHG_EN", "2": "LED_MID", "3": "LED_K"},
     "LED switch 1: on when firmware sets CHG_EN (GPIO5)", "charge", mpn="AO3400A")
part("Q4", "Transistor_FET:Q_NMOS_GSD", "AO3400A", FP_SOT23, {"1": "PSW_EN", "2": "GND", "3": "LED_MID"},
     "LED switch 2: firmware raises PSW_EN (GPIO10) before any switch; both must be on", "charge",
     mpn="AO3400A")
R("R3", "100k", "CHG_EN", "GND", "Keeps CHG_EN low while the ESP32 resets", "charge")
R("R4", "100k", "PSW_EN", "GND", "Keeps PSW_EN low while the ESP32 resets", "charge")
# Voltage dividers: firmware uses (220k+4.7k)/4.7k; 2.2M/47k is the same ratio at 1/10 the drain.
R("R5", "2.2M 1206", "CHG_POS", "VCHG_ADC", "Charger-voltage divider top (charger detect)", "charge", fp=FP_R1206)
R("R6", "47k 1%", "VCHG_ADC", "GND", "Charger-voltage divider bottom", "charge")
C("C1", "100n", "VCHG_ADC", "GND", "ADC filter for the charger voltage", "charge")
R("R7", "2.2M 1206", "PACK_F", "VOUT_ADC", "Pack-voltage divider top (fuse / lead check)", "charge", fp=FP_R1206)
R("R8", "47k 1%", "VOUT_ADC", "GND", "Pack-voltage divider bottom", "charge")
C("C2", "100n", "VOUT_ADC", "GND", "ADC filter for the pack voltage", "charge")


# ---------------------------------------------------------------- power
part("U4", "Regulator_Switching:LTC7138xMSE", "LTC7138", None,
     {"3": "VIN_BUCK", "14": "RUN", "12": "GND", "6": "GND", "7": "GND", "9": "VFB",
      "1": "SW", "16": "ANODE", "8": "GND", "17": "GND"},
     "140 V buck: pack to 5 V for the ESP32, isolators and buzzer", "power",
     nc=["5", "10", "11"], mpn="LTC7138EMSE#PBF")
R("R9", "100R 1206", "PACK_F", "VIN_BUCK", "Buck input RC filter and inrush limit", "power", fp=FP_R1206)
C("C3", "1u 250V", "VIN_BUCK", "GND", "Buck input capacitor", "power", fp=FP_C1210)
C("C4", "1u 250V", "VIN_BUCK", "GND", "Buck input capacitor", "power", fp=FP_C1210)
R("R10", "2.2M 1206", "VIN_BUCK", "RUN", "RUN divider top: starts the buck above ~40 V", "power", fp=FP_R1206)
R("R11", "68k", "RUN", "GND", "RUN divider bottom: keeps RUN under 4.1 V at 134 V", "power")
part("L1", "Device:L", "180uH >=0.7A", "Inductor_SMD:L_7.3x7.3_H4.5", {"1": "SW", "2": "5V_BUCK"},
     "Buck inductor (VBMS uses 180 uH)", "power", mpn="180 uH shielded 7.3x7.3, Isat >= 0.7 A")
part("D2", "Device:D", "ES1D", FP_SMA, {"1": "SW", "2": "ANODE"},
     "Buck catch diode; anode returns through the ANODE sense pin", "power", mpn="ES1D")
R("R12", "1.05M 1%", "5V_BUCK", "VFB", "Feedback top: 0.8 V x (1 + 1.05M/200k) = 5.0 V", "power")
R("R13", "200k 1%", "VFB", "GND", "Feedback bottom", "power")
C("C5", "22u 10V", "5V_BUCK", "GND", "Buck output capacitor", "power", fp=FP_C1206)
part("D3", "Device:D_Schottky", "B5819W", FP_SOD123, {"2": "5V_BUCK", "1": "5V"},
     "OR-ing diode: buck into the 5 V rail", "power", mpn="B5819W")
part("D4", "Device:D_Schottky", "B5819W", FP_SOD123, {"2": "VBUS", "1": "5V"},
     "OR-ing diode: USB into the 5 V rail, so the ESP32 can be flashed without the pack", "power",
     mpn="B5819W")
part("U6", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "5V", "3": "5V", "5": "3V3", "2": "GND"}, "3.3 V LDO for the logic, 600 mA; EN tied on",
     "power", nc=["4"], mpn="AP2112K-3.3TRG1")
C("C6", "10u 10V", "5V", "GND", "LDO input capacitor", "power", fp=FP_C0805)
C("C7", "10u 10V", "3V3", "GND", "LDO output capacitor", "power", fp=FP_C0805)


# ---------------------------------------------------------------- MCU
part("U_ESP1", "qfbms_reva:ESP32-C3-MINI-1", "ESP32-C3-MINI-1", "qfbms_reva:ESP32-C3-MINI-1",
     {"1": "GND", "3": "3V3", "8": "EN", "12": "VCHG_ADC", "13": "VOUT_ADC", "5": "BTN",
      "6": "BUZ", "19": "CHG_EN", "16": "PSW_EN", "20": "CAN_RX", "21": "CAN_TX",
      "22": "GPIO8", "23": "COM_EN", "26": "USB_DN", "27": "USB_DP", "30": "SCL", "31": "SDA"},
     "Runs VESC Express VBMS32 firmware and the Micro package (pins per hw_vbms32.h)", "mcu",
     nc=["18"], mpn="ESP32-C3-MINI-1-N4")
C("C8", "10u 10V", "3V3", "GND", "ESP32 bulk decoupling", "mcu", fp=FP_C0805)
C("C9", "100n", "3V3", "GND", "ESP32 HF decoupling", "mcu")
R("R14", "10k", "3V3", "EN", "EN RC delay, R (Espressif: 10k/1uF)", "mcu")
C("C10", "1u", "EN", "GND", "EN RC delay, C", "mcu", fp=FP_C0603)
R("R15", "10k", "3V3", "GPIO8", "GPIO8 strap high (needed for download boot); PCHG_EN is unused", "mcu")
R("R16", "10k", "3V3", "COM_EN", "GPIO9 strap high = normal boot; also keeps the upper link off at reset", "mcu")
part("TP1", "Connector:TestPoint", "BOOT", "TestPoint:TestPoint_Pad_D1.0mm", {"1": "COM_EN"},
     "Short to GND at power-up for manual download mode", "mcu")
R("R17", "100k", "BTN", "GND", "ENABLE input idles low = 'key off' (firmware: high keeps it awake)", "mcu")
part("SW1", "Switch:SW_Push", "WAKE", "Button_Switch_SMD:SW_SPST_PTS810", {"1": "3V3", "2": "BTN"},
     "Press to wake the BMS from deep sleep (GPIO2 high) for a VESC Tool connection", "mcu")
# Buzzer: firmware runs 4 kHz PWM on GPIO3
part("Q5", "Transistor_BJT:Q_NPN_BEC", "MMBT3904", FP_SOT23, {"1": "BUZ_B", "2": "GND", "3": "BUZ_K"},
     "Buzzer driver", "mcu", mpn="MMBT3904")
R("R18", "1k", "BUZ", "BUZ_B", "Buzzer driver base resistor", "mcu")
R("R19", "10k", "BUZ_B", "GND", "Keeps the buzzer silent during reset", "mcu")
part("BZ1", "Device:Buzzer", "4kHz magnetic", "qfbms_reva:Buzzer_5.0x5.0mm_SMD", {"1": "5V", "2": "BUZ_K"},
     "Status beeper driven by the Micro package", "mcu", mpn="5x5 mm magnetic transducer, 4 kHz, 5 V")
part("D5", "Device:D", "1N4148W", FP_SOD123, {"1": "5V", "2": "BUZ_K"},
     "Flyback clamp for the magnetic buzzer", "mcu", mpn="1N4148W")
# USB
part("J_USB1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "qfbms_reva:USB_C_Receptacle_16P",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS",
      "B9": "VBUS", "A5": "CC1", "B5": "CC2", "A6": "USB_DP_C", "B6": "USB_DP_C", "A7": "USB_DN_C",
      "B7": "USB_DN_C", "SH": "GND"},
     "USB for flashing and VESC Tool (fixed position)", "mcu", nc=["A8", "B8"], fixed=True)
R("R20", "5.1k", "CC1", "GND", "USB-C sink identification (CC1)", "mcu")
R("R21", "5.1k", "CC2", "GND", "USB-C sink identification (CC2)", "mcu")
part("U8", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DP_C", "6": "USB_DP", "3": "USB_DN_C", "4": "USB_DN", "2": "GND", "5": "VBUS"},
     "ESD protection on the USB data lines", "mcu", mpn="USBLC6-2SC6")


# ---------------------------------------------------------------- comms
R("R22", "4.7k", "3V3", "SDA", "Host I2C pull-up (SDA); lower monitor sits on this bus", "comms")
R("R23", "4.7k", "3V3", "SCL", "Host I2C pull-up (SCL)", "comms")
for ref, a, b, what in [("U9", "SDA", "SDA_ISO1", "SDA"), ("U10", "SCL", "SCL_ISO1", "SCL")]:
    part(ref, "74xGxx:74CBTLV1G125", "74CBTLV1G125", "Package_TO_SOT_SMD:SOT-353_SC-70-5",
         {"1": "COM_EN", "2": a, "4": b, "3": "GND", "5": "3V3"},
         f"Bus switch ({what}): hides the upper monitor while COM_EN (GPIO9) is high, "
         "as the firmware's address-change startup needs", "comms", mpn="SN74CBTLV1G125DCKR")
C("C11", "100n", "3V3", "GND", "U9 decoupling", "comms")
C("C12", "100n", "3V3", "GND", "U10 decoupling", "comms")
part("U11", "Isolator:ISO1540", "ISO1640BDR", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "3V3", "2": "SDA_ISO1", "3": "SCL_ISO1", "4": "GND", "5": "CELL16", "6": "SCL_BQ2",
      "7": "SDA_BQ2", "8": "ISO_VCC2"},
     "I2C isolator to the upper monitor (CELL16 domain); ISO1640 = ISO1540 pinout", "comms",
     mpn="ISO1640BDR")
C("C13", "100n", "3V3", "GND", "ISO1640 side-1 decoupling", "comms")
C("C14", "100n", "ISO_VCC2", "CELL16", "ISO1640 side-2 decoupling", "comms")
R("R24", "4.7k", "3V3", "SDA_ISO1", "Side-1 pull-up (SDA) between switch and isolator", "comms")
R("R25", "4.7k", "3V3", "SCL_ISO1", "Side-1 pull-up (SCL)", "comms")
R("R26", "4.7k", "ISO_VCC2", "SDA_BQ2", "Upper-monitor bus pull-up (SDA)", "comms")
R("R27", "4.7k", "ISO_VCC2", "SCL_BQ2", "Upper-monitor bus pull-up (SCL)", "comms")
# Isolator side 2 runs from the upper monitor's REG1 only while COM_EN is low,
# so the top 16 cells are not drained by the isolator during deep sleep.
part("U12", "Isolator:PC817", "VOMA617A", FP_SOP4, {"1": "COM_LED_A", "2": "COM_EN", "4": "ISO_PG", "3": "CELL16"},
     "Opto: COM_EN low turns on the isolator's upper-side supply", "comms", mpn="VOMA617A-3X001T")
R("R28", "1k", "3V3", "COM_LED_A", "Opto LED current, ~2 mA (sunk by GPIO9 low)", "comms")
part("Q6", "Transistor_FET:Q_PMOS_GSD", "AO3401A", FP_SOT23, {"1": "ISO_PG", "2": "REG1_BQ2", "3": "ISO_VCC2"},
     "Switches upper REG1 to the isolator side 2", "comms", mpn="AO3401A")
R("R29", "100k", "REG1_BQ2", "ISO_PG", "Holds Q6 off unless the opto pulls its gate", "comms")
# CAN
part("U7", "Interface_CAN_LIN:ISO1050DUB", "ISO1050DUB", None,
     {"1": "3V3", "2": "CAN_RX", "3": "CAN_TX", "4": "GND", "5": "ISO_GND", "6": "CANL", "7": "CANH",
      "8": "5V_EXT"}, "Isolated CAN transceiver to the VESC", "comms", mpn="ISO1050DUBR")
C("C15", "100n", "3V3", "GND", "ISO1050 side-1 decoupling", "comms")
C("C16", "100n", "5V_EXT", "ISO_GND", "ISO1050 side-2 decoupling", "comms")
R("R30", "10k", "3V3", "CAN_TX", "Holds CAN recessive while the ESP32 sleeps or resets", "comms")
part("J_COMM1", "Connector_Generic:Conn_01x04", "CAN/5V",
     "Connector_JST:JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical",
     {"1": "CANH", "2": "CANL", "3": "ISO_GND", "4": "5V_EXT"},
     "CAN bus to the VESC; the VESC supplies 5 V for the bus side (fixed position)", "comms", fixed=True)
R("R31", "120R", "CANH", "CAN_TERM", "Optional CAN termination", "comms")
part("JP1", "Jumper:SolderJumper_2_Open", "TERM", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "CAN_TERM", "2": "CANL"}, "Close to terminate the CAN bus at the BMS", "comms")
