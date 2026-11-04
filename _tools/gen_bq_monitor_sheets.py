# Generates the QFBMS monitor schematic increment only.
# Does not read or write qfbms32.kicad_pcb, qfbms32.kicad_sch, or qfbms32.kicad_pro.
import os
import json
import math
import re
import uuid
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYM = Path(os.environ.get("KICAD10_SYMBOL_DIR", r"C:\Program Files\KiCad\10.0\share\kicad\symbols"))
FP_EP = "Package_QFP:TQFP-48-1EP_7x7mm_P0.5mm_EP5x5mm_ThermalVias"
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_SOT23_5 = "Package_TO_SOT_SMD:SOT-23-5"
FP_VSSOP8 = "Package_SO:VSSOP-8_3x3mm_P0.65mm"
FP_VSSOP10 = "Package_SO:TSSOP-10_3x3mm_P0.5mm"

ROOT_UUID = "b7c1a0e2-4d55-4a1e-9c31-0f6a2b8d1001"
LOWER_SHEET = "c4e8b21a-7f63-4d18-a902-11d6e5a72011"
UPPER_SHEET = "d91f06c4-2ab8-4e77-b5c3-88a14f903022"
LOWER_FILE = "e2a64c90-15db-4f42-9e18-77c0b3d54133"
UPPER_FILE = "f30b58d1-86ac-4c29-a1e7-64d9e2f85244"
ISO_SHEET = "a18c44e0-6b21-4f55-9d30-2c7e91ab6044"
ISO_FILE = "b29d55f1-7c32-4056-ae41-3d8f02bc7155"
PROJECT = "qfbms32-bq-monitors"


IDENTITIES = json.loads((Path(__file__).with_name("bq-monitor-identities.json")).read_text())


def uid(key):
    return IDENTITIES.get(key, str(uuid.uuid5(uuid.UUID(ROOT_UUID), key)))


def snap(v):
    return round(round(float(v) / 1.27) * 1.27, 2)


def rnd(p):
    return (snap(p[0]), snap(p[1]))


def xform(local, origin, angle):
    """Map a symbol-file pin onto the schematic.

    KiCad's zero-rotation transform negates symbol Y. Rotations 90 and 180
    were checked against the netlist for the resistor and diode symbols.
    """
    x, y = local
    a = angle % 360
    if a == 0:
        return rnd((origin[0] + x, origin[1] - y))
    rad = math.radians(a)
    return rnd((
        origin[0] + x * math.cos(rad) - y * math.sin(rad),
        origin[1] + x * math.sin(rad) + y * math.cos(rad),
    ))


def sexpr_str(text):
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    return '"' + escaped + '"'


def extract_symbol(path, name):
    text = path.read_text(encoding="utf-8")
    token = f'(symbol "{name}"'
    start = 0
    while True:
        i = text.find(token, start)
        if i < 0:
            raise SystemExit(f"symbol not found: {name}")
        nxt = text[i + len(token)]
        if nxt in "\r\n\t ":
            break
        start = i + 1
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    raise SystemExit(f"unclosed symbol {name}")


def parse_pins(symbol_text):
    pins = {}
    for match in re.finditer(
        r"\(pin\s+\S+\s+line\s+\(at\s+([-0-9.]+)\s+([-0-9.]+)\s+[-0-9.]+\)[\s\S]*?\(number\s+\"(\d+)\"",
        symbol_text,
    ):
        pins[match.group(3)] = (float(match.group(1)), float(match.group(2)))
    return pins


def prepare_bq():
    sym = extract_symbol(SYM / "Battery_Management.kicad_sym", "BQ76952PFB")
    sym = sym.replace('(symbol "BQ76952PFB_1_1"', '(symbol "BQ7695202PFB_1_1"', 1)
    sym = sym.replace(
        '(symbol "BQ76952PFB"',
        '(symbol "qfbms:BQ7695202PFB"',
        1,
    )
    sym = sym.replace(
        '(property "Value" "BQ76952PFB"',
        '(property "Value" "BQ7695202PFB"',
        1,
    )
    sym = sym.replace(
        "I2C interface without CRC, REG1 LDO disabled",
        "I2C interface with CRC, REG1 default 3.3 V",
    )
    sym = sym.replace(
        "Package_QFP:TQFP-48_7x7mm_P0.5mm",
        FP_EP,
    )
    sym, n19 = re.subn(
        r"(\(pin no_connect line\s+\(at )-17\.78 -40\.64( 0\)\s+\(length 2\.54\)\s+)\(hide yes\)\s*",
        r"\g<1>-20.32 -25.4\2",
        sym,
        count=1,
    )
    sym, n44 = re.subn(
        r"(\(pin no_connect line\s+\(at )-17\.78 -38\.1( 0\)\s+\(length 2\.54\)\s+)\(hide yes\)\s*",
        r"\g<1>-20.32 -27.94\2",
        sym,
        count=1,
    )
    if n19 != 1 or n44 != 1:
        raise SystemExit(f"NC pin edit failed {n19} {n44}")
    ep = """
			(pin power_in line
				(at 0 -45.72 90)
				(length 2.54)
				(name "EP"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
				(number "49"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
			)"""
    marker = "\t\t)\n\t\t(embedded_fonts no)"
    idx = sym.rfind(marker)
    if idx < 0:
        raise SystemExit("BQ unit close not found")
    sym = sym[:idx] + ep + "\n" + sym[idx:]
    pins = parse_pins(sym)
    if set(pins) != {str(i) for i in range(1, 50)}:
        raise SystemExit(f"BQ pins {sorted(pins, key=int)}")
    return sym, pins


def rename_power(symbol_text, lib_name, value, unit_prefix):
    text = symbol_text
    text = text.replace('(symbol "GND_0_1"', f'(symbol "{unit_prefix}_0_1"', 1)
    text = text.replace('(symbol "GND_1_1"', f'(symbol "{unit_prefix}_1_1"', 1)
    text = text.replace('(symbol "GND"', f'(symbol "{lib_name}"', 1)
    text = text.replace('(property "Value" "GND"', f'(property "Value" "{value}"', 1)
    return text


def load_libs():
    bq, bq_pins = prepare_bq()
    gnd = extract_symbol(SYM / "power.kicad_sym", "GND")
    flag = extract_symbol(SYM / "power.kicad_sym", "PWR_FLAG")
    flag = flag.replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)
    vcc = embed(extract_symbol(SYM / "power.kicad_sym", "VCC"), "power:VCC")
    iso = extract_symbol(SYM / "Isolator.kicad_sym", "ISO1540")
    iso = iso.replace('(symbol "ISO1540_0_1"', '(symbol "ISO1640_D8_0_1"', 1)
    iso = iso.replace('(symbol "ISO1540_1_1"', '(symbol "ISO1640_D8_1_1"', 1)
    iso = iso.replace('(symbol "ISO1540"', '(symbol "qfbms:ISO1640_D8"', 1)
    iso = iso.replace('(property "Value" "ISO1540"', '(property "Value" "ISO1640"', 1)
    iso = iso.replace(
        'http://www.ti.com/lit/ds/symlink/iso1541.pdf',
        'https://www.ti.com/lit/ds/symlink/iso1640.pdf',
        1,
    )
    bus_switch = make_tmux154e_symbol()
    iso = iso.replace(
        "I2C Isolator, 2.5 kVrms, Bidirectional clock and data, SOIC-8",
        "ISO1640 8-D pin map, bidirectional SDA and SCL, no enable pin. Orderable suffix is not selected.",
        1,
    )
    libs = {
        "qfbms:BQ7695202PFB": bq,
        "Device:R": embed(extract_symbol(SYM / "Device.kicad_sym", "R"), "Device:R"),
        "Device:C": embed(extract_symbol(SYM / "Device.kicad_sym", "C"), "Device:C"),
        "Device:D": embed(extract_symbol(SYM / "Device.kicad_sym", "D"), "Device:D"),
        "Device:Thermistor": embed(
            extract_symbol(SYM / "Device.kicad_sym", "Thermistor"), "Device:Thermistor"
        ),
        "Transistor_BJT:Q_NPN_BCE": embed(
            extract_symbol(SYM / "Transistor_BJT.kicad_sym", "Q_NPN_BCE"),
            "Transistor_BJT:Q_NPN_BCE",
        ),
        "power:GND": embed(gnd, "power:GND"),
        "power:VCC": vcc,
        "power:PWR_FLAG": flag,
        "qfbms:ISO1640_D8": iso,
        "qfbms:TMUX154E": bus_switch,
    }
    GEOM["qfbms:ISO1640_D8"] = parse_pins(iso)
    GEOM["qfbms:TMUX154E"] = parse_pins(bus_switch)
    return libs, bq_pins


def embed(text, lib_id):
    name = lib_id.split(":")[-1]
    return text.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)


def make_tmux154e_symbol():
    """Small explicit symbol using the TI TMUX154E DGS 10-pin map."""
    pins = [
        ("passive", "A0", "2", -15.24, 5.08, 0),
        ("passive", "A1", "3", -15.24, 0, 0),
        ("passive", "A", "4", 15.24, 5.08, 180),
        ("power_in", "GND", "5", -5.08, -12.7, 90),
        ("passive", "B", "6", 15.24, -2.54, 180),
        ("passive", "B1", "7", 15.24, -7.62, 180),
        ("passive", "B0", "8", -15.24, -2.54, 0),
        ("input", "EN", "9", -5.08, 12.7, 270),
        ("power_in", "VCC", "10", 5.08, 12.7, 270),
        ("input", "SEL", "1", 5.08, -12.7, 90),
    ]
    pin_text = []
    for kind, name, number, x, y, angle in pins:
        pin_text.append(
                f'''\t\t\t(pin {kind} line (at {x} {y} {angle}) (length 5.08)
\t\t\t\t(name "{name}" (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t\t(number "{number}" (effects (font (size 1.27 1.27))))
\t\t\t)'''
        )
    return f'''(symbol "qfbms:TMUX154E"
\t(property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
\t(property "Value" "TMUX154E" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
\t(property "Footprint" "{FP_VSSOP10}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t(property "Datasheet" "https://www.ti.com/lit/ds/symlink/tmux154e.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t(symbol "TMUX154E_0_1"
\t\t(rectangle (start -10.16 10.16) (end 10.16 -10.16)
\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))
\t)
\t(symbol "TMUX154E_1_1"
{chr(10).join(pin_text)}
\t)
)'''


GEOM = {
    "Device:R": {"1": (0.0, 3.81), "2": (0.0, -3.81)},
    "Device:C": {"1": (0.0, 3.81), "2": (0.0, -3.81)},
    "Device:D": {"1": (-3.81, 0.0), "2": (3.81, 0.0)},
    "Device:Thermistor": {"1": (0.0, 5.08), "2": (0.0, -5.08)},
    "Transistor_BJT:Q_NPN_BCE": {
        "1": (-5.08, 0.0),
        "2": (2.54, 5.08),
        "3": (2.54, -5.08),
    },
    "power:GND": {"1": (0.0, 0.0)},
    "power:VCC": {"1": (0.0, 0.0)},
    "power:PWR_FLAG": {"1": (0.0, 0.0)},
}


class Sch:
    def __init__(self, file_uuid, paper, title, comment, page):
        self.file_uuid = file_uuid
        self.paper = paper
        self.title = title
        self.comment = comment
        self.page = page
        self.libs = []
        self.body = []
        self.wires = []
        self.used_libs = []
        self.opens = []
        self.pin_points = []
        self.endpoints = []

    def use(self, lib_id, catalog):
        if lib_id not in self.used_libs:
            self.used_libs.append(lib_id)
            self.libs.append(catalog[lib_id])

    def add(self, text):
        self.body.append(text)

    def wire(self, a, b):
        a, b = rnd(a), rnd(b)
        if a == b:
            return a
        if a[0] != b[0] and a[1] != b[1]:
            raise ValueError(f"diagonal wire {a} -> {b}")
        self.wires.append((a, b))
        self.endpoints.extend((a, b))
        return b

    def elbow(self, a, b, horizontal_first=True):
        a, b = rnd(a), rnd(b)
        if a[0] == b[0] or a[1] == b[1]:
            self.wire(a, b)
            return
        mid = (b[0], a[1]) if horizontal_first else (a[0], b[1])
        self.wire(a, mid)
        self.wire(mid, b)

    def label(self, name, at, angle=0, kind="local", shape="passive"):
        at = rnd(at)
        self.endpoints.append(at)
        justify = "left" if angle == 0 else "right"
        effects = f"""(effects
			(font
				(size 1.27 1.27)
			)
			(justify {justify})
		)"""
        if kind == "local":
            self.add(
                f"""	(label {sexpr_str(name)}
		(at {at[0]} {at[1]} {angle})
		(fields_autoplaced yes)
		{effects}
		(uuid "{uid(f"{self.file_uuid}:label:{kind}:{name}:{at}:{angle}")}")
	)"""
            )
        elif kind == "global":
            self.add(
                f"""	(global_label {sexpr_str(name)}
		(shape {shape})
		(at {at[0]} {at[1]} {angle})
		(fields_autoplaced yes)
		{effects}
		(uuid "{uid(f"{self.file_uuid}:label:{kind}:{name}:{at}:{angle}")}")
		(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
			(at {at[0]} {at[1]} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
	)"""
            )
        elif kind == "hier":
            self.add(
                f"""	(hierarchical_label {sexpr_str(name)}
		(shape {shape})
		(at {at[0]} {at[1]} {angle})
		{effects}
		(uuid "{uid(f"{self.file_uuid}:label:{kind}:{name}:{at}:{angle}")}")
	)"""
            )
        else:
            raise ValueError(kind)
        return at

    def noconn(self, at):
        at = rnd(at)
        self.endpoints.append(at)
        self.add(f'\t(no_connect (at {at[0]} {at[1]}) (uuid "{uid(f"{self.file_uuid}:nc:{at}")}"))')
        return at

    def text(self, at, text, size=1.27):
        at = rnd(at)
        self.add(
            f"""	(text {sexpr_str(text)}
		(at {at[0]} {at[1]} 0)
		(effects
			(font
				(size {size} {size})
			)
			(justify left top)
		)
		(uuid "{uid(f"{self.file_uuid}:text:{at}")}")
	)"""
        )

    def part(self, catalog, lib_id, at, rot, ref, value, footprint, pins, path, bom=True):
        self.use(lib_id, catalog)
        at = rnd(at)
        identity = ref if bom else f"power:{lib_id}:{at}"
        world = {}
        pin_lines = []
        for number, local in pins.items():
            xy = xform(local, at, rot)
            world[number] = xy
            self.pin_points.append(xy)
            pin_lines.append(f'\t\t(pin "{number}" (uuid "{uid(f"{self.file_uuid}:pin:{identity}:{number}")}"))')
        ref_at = (at[0] + 4.0, at[1] + 1.5)
        val_at = (at[0] + 4.0, at[1] - 1.5)
        if rot == 90:
            ref_at = (at[0], at[1] + 3.2)
            val_at = (at[0], at[1] - 3.2)
        bom_s = "yes" if bom else "no"
        board_s = "yes" if bom else "no"
        self.add(
            f"""	(symbol
		(lib_id "{lib_id}")
		(at {at[0]} {at[1]} {rot})
		(unit 1)
		(body_style 1)
		(exclude_from_sim no)
		(in_bom {bom_s})
		(on_board {board_s})
		(in_pos_files {board_s})
		(dnp no)
		(uuid "{uid(f"{self.file_uuid}:part:{identity}")}")
		(property "Reference" "{ref}"
			(at {ref_at[0]} {ref_at[1]} 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Value" "{value}"
			(at {val_at[0]} {val_at[1]} 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "{footprint}"
			(at {at[0]} {at[1]} 0)
			(hide yes)
			(effects (font (size 1.27 1.27)))
		)
		(property "Datasheet" "~"
			(at {at[0]} {at[1]} 0)
			(hide yes)
			(effects (font (size 1.27 1.27)))
		)
		{chr(10).join(pin_lines)}
		(instances
			(project "{PROJECT}"
				(path "{path}"
					(reference "{ref}")
					(unit 1)
				)
			)
		)
	)"""
        )
        if not bom:
            self.body[-1] = self.body[-1].replace('(effects (font (size 1.27 1.27)))', '(effects (font (size 1.27 1.27)) (hide yes))', 1)
        return world

    def finish(self):
        counts = {}
        for pt in self.wires and [p for seg in self.wires for p in seg]:
            counts[pt] = counts.get(pt, 0) + 1
        for pt, count in counts.items():
            if count >= 3:
                self.add(
                    f"""	(junction
		(at {pt[0]} {pt[1]})
		(diameter 0)
		(color 0 0 0 0)
		(uuid "{uid(f"{self.file_uuid}:junction:{pt}")}")
	)"""
                )
        wire_txt = []
        seen = set()
        for a, b in self.wires:
            key = (a, b)
            if key in seen or (b, a) in seen:
                continue
            seen.add(key)
            wire_txt.append(
                f"""	(wire
		(pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]}))
		(stroke (width 0) (type default))
		(uuid "{uid(f"{self.file_uuid}:wire:{sorted((a, b))}")}")
	)"""
            )
        libs = "\n".join(self.indent_lib(lib) for lib in self.libs)
        return f"""(kicad_sch
	(version 20260101)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "{self.file_uuid}")
	(paper "{self.paper}")
	(title_block
		(title {sexpr_str(self.title)})
		(date "2026-11-03")
		(rev "0.1")
		(comment 1 {sexpr_str(self.comment)})
	)
	(lib_symbols
{libs}
	)
{chr(10).join(wire_txt)}
{chr(10).join(self.body)}
	(sheet_instances
		(path "/"
			(page "{self.page}")
		)
	)
	(embedded_fonts no)
)
"""

    @staticmethod
    def indent_lib(text):
        return "\n".join("\t\t" + line if line else line for line in text.splitlines())


def gnd(sch, catalog, net, at, path, nref):
    pins = sch.part(
        catalog,
        "power:GND",
        at,
        0,
        f"#PWR{nref[0]:04d}",
        net,
        "",
        GEOM["power:GND"],
        path,
        bom=False,
    )
    nref[0] += 1
    return pins["1"]


def flag(sch, catalog, at, path, nref):
    pins = sch.part(
        catalog,
        "power:PWR_FLAG",
        at,
        0,
        f"#FLG{nref[0]:04d}",
        "PWR_FLAG",
        "",
        GEOM["power:PWR_FLAG"],
        path,
        bom=False,
    )
    nref[0] += 1
    return pins["1"]


def build_monitor_sheet(upper, catalog, bq_pins):
    if upper:
        file_uuid = UPPER_FILE
        path = f"/{ROOT_UUID}/{UPPER_SHEET}"
        page = "3"
        ref_ic = "U_BQ2"
        vss = "CELL16"
        title = "QFBMS32 upper monitor U_BQ2"
        cell0 = 16
        rbase = 101
        cbase = 101
        dbase = 101
        qref = "Q101"
        rt_base = None
    else:
        file_uuid = LOWER_FILE
        path = f"/{ROOT_UUID}/{LOWER_SHEET}"
        page = "2"
        ref_ic = "U_BQ1"
        vss = "CELL0"
        title = "QFBMS32 lower monitor U_BQ1"
        cell0 = 0
        rbase = 1
        cbase = 1
        dbase = 1
        qref = "Q1"
        rt_base = 1
    sch = Sch(
        file_uuid,
        "A1",
        title,
        "Charge-only monitor sheet. Do not import this netlist into qfbms32.kicad_pcb.",
        page,
    )
    nref = [1 if not upper else 301]
    opens = []

    def mark(ref, function):
        opens.append(f"{ref}: {function}")

    ic = (368.3, 228.6)
    sch.part(
        catalog,
        "qfbms:BQ7695202PFB",
        ic,
        0,
        ref_ic,
        "BQ7695202",
        FP_EP,
        bq_pins,
        path,
    )
    sch.body[-1] = sch.body[-1].replace(
        f'(at {ic[0] + 4.0} {ic[1] + 1.5} 0)',
        f'(at {ic[0] - 18} {ic[1] + 50} 0)',
        1,
    )
    sch.body[-1] = sch.body[-1].replace(
        f'(at {ic[0] + 4.0} {ic[1] - 1.5} 0)',
        f'(at {ic[0] + 16} {ic[1] + 50} 0)',
        1,
    )
    bq = {num: xform(local, ic, 0) for num, local in bq_pins.items()}

    def pwr(net, at):
        return gnd(sch, catalog, net, at, path, nref)

    def lab(name, at, angle=0, kind="local", shape="passive"):
        return sch.label(name, at, angle, kind, shape)

    def stub(number, name, dx, kind="local", shape="passive"):
        x, y = bq[number]
        dest = (x + dx, y)
        sch.wire((x, y), dest)
        angle = 0 if dx >= 0 else 180
        lab(name, dest, angle, kind, shape)
        return dest

    # --- cell filters: 20 ohm + 220 nF, copied from SLUSE13B 7.3 and EVM 5.4 ---
    base_y = 88.9
    step = 12.7
    y_of = {n: round(base_y + n * step, 2) for n in range(17)}
    rx = 127.0
    cap_x = 165.1
    for n in range(17):
        y = y_of[n]
        pins = sch.part(
            catalog, "Device:R", (rx, y), 90,
            f"R{rbase + n}", "20", "", GEOM["Device:R"], path,
        )
        cell = f"CELL{cell0 + n}"
        left = lab(cell, (pins["1"][0] - 15.24, y), 180, "global")
        sch.wire(left, pins["1"])
        node = (cap_x, y)
        sch.wire(pins["2"], node)
        lab(f"VCF{n}", (pins["2"][0] + 6, y), 0, "local")
    for n in range(16, 0, -1):
        top, bot = y_of[n], y_of[n - 1]
        pins = sch.part(
            catalog, "Device:C", (cap_x, round((top + bot) / 2, 2)), 0,
            f"C{cbase + (16 - n)}", "220nF", FP_C0603, GEOM["Device:C"], path,
        )
        sch.wire((cap_x, top), pins["1"])
        sch.wire(pins["2"], (cap_x, bot))
    c_vc0 = sch.part(
        catalog, "Device:C", (cap_x + 17.78, y_of[0]), 90,
        f"C{cbase + 16}", "220nF", FP_C0603, GEOM["Device:C"], path,
    )
    sch.wire((cap_x, y_of[0]), c_vc0["1"])
    lab("VCF0", c_vc0["1"], 180, "local")
    vg = pwr(vss, (c_vc0["2"][0] + 8, c_vc0["2"][1]))
    sch.wire(c_vc0["2"], vg)

    # VC pin numbers: 48=VC16, 1=VC15 ... 15=VC1, 16=VC0.
    stub("48", "VCF16", -12.7)
    for vc in range(15, 0, -1):
        stub(str(16 - vc), f"VCF{vc}", -12.7)
    stub("16", "VCF0", -12.7)

    # VSS and exposed pad.
    vss_pt = bq["17"]
    ep = bq["49"]
    bus_x = vss_pt[0] - 20.32
    sch.wire(vss_pt, (vss_pt[0], vss_pt[1] - 7.62))
    sch.wire((vss_pt[0], vss_pt[1] - 7.62), (bus_x, vss_pt[1] - 7.62))
    sch.wire(ep, (ep[0], vss_pt[1] - 7.62))
    g_ic = pwr(vss, (bus_x, vss_pt[1] - 12.7))
    sch.wire((bus_x, vss_pt[1] - 7.62), g_ic)
    flag(sch, catalog, (bus_x - 10.16, vss_pt[1] - 12.7), path, nref)
    sch.wire((bus_x - 10.16, vss_pt[1] - 12.7), g_ic)

    # --- supply: BAT, REG0, REG18, REG1, CP1 ---
    stack = f"CELL{cell0 + 16}"
    sx, sy = 470.0, 470.0
    stack_pt = lab(stack, (sx, sy), 180, "global")
    d_bat = sch.part(
        catalog, "Device:D", (sx + 25.4, sy), 180,
        f"D{dbase}", "OPEN", "", GEOM["Device:D"], path,
    )
    mark(f"D{dbase}", "BAT series diode. MPN, voltage rating, and footprint are OPEN. Separate from the REG0 collector diode (SLUSE13B 16.2).")
    sch.wire(stack_pt, d_bat["2"])  # anode, rotation 180
    r_bat = sch.part(
        catalog, "Device:R", (sx + 48, sy), 90,
        f"R{rbase + 17}", "100", "", GEOM["Device:R"], path,
    )
    sch.wire(d_bat["1"], r_bat["1"])
    bat_node = (r_bat["2"][0] + 8, sy)
    sch.wire(r_bat["2"], bat_node)
    lab("BAT_PIN", bat_node, 0, "local")
    for i, (val, fp, dx) in enumerate((("1uF", "", 0), ("100pF", "", 12))):
        cap = sch.part(
            catalog, "Device:C", (bat_node[0] + dx, sy - 12), 0,
            f"C{cbase + 17 + i}", val, fp, GEOM["Device:C"], path,
        )
        sch.wire((bat_node[0] + dx, sy), cap["1"])
        if dx:
            sch.wire(bat_node, (bat_node[0] + dx, sy))
        gg = pwr(vss, (cap["2"][0], cap["2"][1] - 6))
        sch.wire(cap["2"], gg)
    stub("47", "BAT_PIN", 15.24)
    stub("46", "BAT_PIN", 15.24)

    # REG0 NPN. Collector diode from the same stack node, not the BAT diode.
    q = sch.part(
        catalog, "Transistor_BJT:Q_NPN_BCE", (sx + 25.4, sy - 40), 0,
        qref, "OPEN", "", GEOM["Transistor_BJT:Q_NPN_BCE"], path,
    )
    mark(qref, "REG0 NPN. MPN and footprint are OPEN. Collector-emitter must tolerate this monitor's own stack, not the full 32s pack.")
    d_col = sch.part(
        catalog, "Device:D", (q["2"][0] - 3.81, q["2"][1] + 12), 180,
        f"D{dbase + 1}", "OPEN", "", GEOM["Device:D"], path,
    )
    mark(f"D{dbase + 1}", "REG0 collector diode. MPN, voltage rating, and footprint are OPEN.")
    sch.wire(d_col["1"], q["2"])
    sch.elbow(stack_pt, d_col["2"], horizontal_first=False)
    breg = lab("BREG", (q["1"][0] - 12, q["1"][1]), 180, "local")
    sch.wire(breg, q["1"])
    r_breg = sch.part(
        catalog, "Device:R", (q["1"][0] - 12, q["1"][1] - 12), 0,
        f"R{rbase + 18}", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 18}", "BREG-to-VSS resistor. SLUSE13B 16.2.2 says a large resistor such as 10 MOhm; the value is not otherwise fixed.")
    sch.wire(breg, r_breg["1"])
    gg = pwr(vss, (r_breg["2"][0], r_breg["2"][1] - 6))
    sch.wire(r_breg["2"], gg)
    regin = lab("REGIN", (q["3"][0] + 12, q["3"][1]), 0, "local")
    sch.wire(q["3"], regin)
    c_regin = sch.part(
        catalog, "Device:C", (q["3"][0] + 12, q["3"][1] - 12), 0,
        f"C{cbase + 19}", "22nF", FP_C0603, GEOM["Device:C"], path,
    )
    sch.wire(regin, c_regin["1"])
    gg = pwr(vss, (c_regin["2"][0], c_regin["2"][1] - 6))
    sch.wire(c_regin["2"], gg)
    stub("37", "BREG", 20.32)
    stub("36", "REGIN", 20.32)

    c_reg18 = sch.part(
        catalog, "Device:C", (bq["24"][0] + 28, bq["24"][1] - 10), 0,
        f"C{cbase + 20}", "2.2uF", FP_C0603, GEOM["Device:C"], path,
    )
    reg18 = stub("24", "REG18", 12.7)
    sch.elbow(reg18, c_reg18["1"])
    gg = pwr(vss, (c_reg18["2"][0], c_reg18["2"][1] - 6))
    sch.wire(c_reg18["2"], gg)

    c_reg1 = sch.part(
        catalog, "Device:C", (bq["35"][0] + 36, bq["35"][1] - 10), 0,
        f"C{cbase + 21}", "1uF", FP_C0603, GEOM["Device:C"], path,
    )
    reg1_net = "REG1_BQ2" if upper else "REG1"
    reg1_kind = "hier" if upper else "local"
    reg1 = stub("35", reg1_net, 12.7, reg1_kind, "bidirectional" if upper else "passive")
    sch.elbow(reg1, c_reg1["1"])
    gg = pwr(vss, (c_reg1["2"][0], c_reg1["2"][1] - 6))
    sch.wire(c_reg1["2"], gg)

    # I2C pull-ups on this domain's REG1.
    # Angle 0 places pin 2 above the symbol center and pin 1 below it.
    i2c_x = 558.8
    i2c_y = 360.68
    lab(reg1_net, (i2c_x, i2c_y), 180, reg1_kind, "bidirectional" if upper else "passive")
    sda_r = sch.part(
        catalog, "Device:R", (i2c_x + 15.24, i2c_y - 3.81), 0,
        f"R{rbase + 19}", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    scl_r = sch.part(
        catalog, "Device:R", (i2c_x + 30.48, i2c_y - 3.81), 0,
        f"R{rbase + 20}", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 19}", "SDA pull-up to this domain's REG1. Resistance is OPEN; the bus is 100 kHz and the capacitance is not yet fixed.")
    mark(f"R{rbase + 20}", "SCL pull-up to this domain's REG1. Resistance is OPEN.")
    sch.wire((i2c_x, i2c_y), sda_r["2"])
    sch.wire(sda_r["2"], scl_r["2"])
    if upper:
        sda_name, scl_name = "SDA_BQ2", "SCL_BQ2"
    else:
        sda_name, scl_name = "SDA_HOST", "SCL_HOST"
    sda_h = lab(sda_name, (sda_r["1"][0], sda_r["1"][1] - 7.62), 270, "hier", "bidirectional")
    scl_h = lab(scl_name, (scl_r["1"][0], scl_r["1"][1] - 7.62), 270, "hier", "bidirectional")
    sch.wire(sda_r["1"], sda_h)
    sch.wire(scl_r["1"], scl_h)
    stub("27", sda_name, 25.4, "hier", "bidirectional")
    stub("26", scl_name, 25.4, "hier", "bidirectional")

    # PACK through 10k to local top of stack.
    r_pack = sch.part(
        catalog, "Device:R", (bq["42"][0] + 25, bq["42"][1]), 90,
        f"R{rbase + 21}", "10k", "", GEOM["Device:R"], path,
    )
    sch.wire(bq["42"], r_pack["1"])
    pack_stack = lab(stack, (r_pack["2"][0] + 12, r_pack["2"][1]), 0, "global")
    sch.wire(r_pack["2"], pack_stack)

    # Wake pins. Upstream sources are sheet ports.
    r_rst = sch.part(
        catalog, "Device:R", (bq["33"][0] - 20, bq["33"][1]), 90,
        f"R{rbase + 22}", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 22}", "RST_SHUT pulldown to local VSS. SLUSE13B 12.6 requires the pin low in normal operation; the resistor value is not specified. The upstream driver is the sheet port.")
    sch.wire(bq["33"], r_rst["2"])
    gg = pwr(vss, (r_rst["1"][0], r_rst["1"][1] + 6))
    sch.wire(r_rst["1"], gg)
    rst_name = "RST_SHUT_BQ2" if upper else "RST_SHUT_BQ1"
    rst_h = lab(rst_name, (bq["33"][0] - 35, bq["33"][1]), 180, "hier", "bidirectional")
    sch.wire(rst_h, bq["33"])

    ts2_name = "TS2_WAKE_BQ2" if upper else "TS2_WAKE_BQ1"
    ts2_h = lab(ts2_name, (bq["22"][0] - 20, bq["22"][1]), 180, "hier", "bidirectional")
    sch.wire(bq["22"], ts2_h)

    r_ld = sch.part(
        catalog, "Device:R", (bq["41"][0] + 18, bq["41"][1]), 90,
        f"R{rbase + 23}", "OPEN", "", GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 23}", "LD series resistor. Value, MPN, and footprint are OPEN. SSZT191 allows wake from LD only with the voltage limited to the datasheet range versus this domain's VSS.")
    sch.wire(bq["41"], r_ld["1"])
    ld_name = "LD_WAKE_BQ2" if upper else "LD_WAKE_BQ1"
    ld_h = lab(ld_name, (r_ld["2"][0] + 12, r_ld["2"][1]), 0, "hier", "bidirectional")
    sch.wire(r_ld["2"], ld_h)

    # Current inputs.
    if upper:
        for number in ("18", "20"):
            pt = bq[number]
            gg = pwr(vss, (pt[0] - 15, pt[1]))
            sch.wire(pt, gg)
    else:
        # One shunt. SRP is the CELL0 end and SRN is the CHG- end.
        shunt = sch.part(
            catalog, "Device:R", (222.25, 50.8), 90,
            "R_SH", "OPEN", "", GEOM["Device:R"], path,
        )
        mark("R_SH", "Single charge-current shunt. Value, MPN, and footprint are OPEN. Do not copy the R001 silkscreen and do not put the existing shunt footprints in series.")
        cell0_pt = lab("CELL0", (shunt["1"][0] - 12.7, shunt["1"][1]), 180, "global")
        sch.wire(cell0_pt, shunt["1"])
        chg = lab("CHG_NEG", (shunt["2"][0] + 12.7, shunt["2"][1]), 0, "hier", "bidirectional")
        sch.wire(shunt["2"], chg)
        r_srp = sch.part(
            catalog, "Device:R", (shunt["1"][0], shunt["1"][1] + 15.24), 0,
            f"R{rbase + 24}", "100", FP_R0603, GEOM["Device:R"], path,
        )
        r_srn = sch.part(
            catalog, "Device:R", (shunt["2"][0], shunt["2"][1] + 15.24), 0,
            f"R{rbase + 25}", "100", FP_R0603, GEOM["Device:R"], path,
        )
        sch.wire(shunt["1"], r_srp["1"])
        sch.wire(shunt["2"], r_srn["1"])
        srp = lab("SRP_NET", (r_srp["2"][0], r_srp["2"][1] + 7.62), 90, "local")
        srn = lab("SRN_NET", (r_srn["2"][0], r_srn["2"][1] + 7.62), 90, "local")
        sch.wire(r_srp["2"], srp)
        sch.wire(r_srn["2"], srn)
        c_sense = sch.part(
            catalog, "Device:C", ((r_srp["2"][0] + r_srn["2"][0]) / 2, r_srp["2"][1]), 90,
            f"C{cbase + 22}", "100nF", FP_C0603, GEOM["Device:C"], path,
        )
        sch.wire(c_sense["1"], r_srp["2"])
        sch.wire(c_sense["2"], r_srn["2"])
        stub("18", "SRP_NET", -17.78)
        stub("20", "SRN_NET", -17.78)

    # Temperature or unused multifunction pins.
    if not upper:
        channels = [
            ("21", "TS1", "RT1", rbase + 26),
            ("23", "TS3", "RT2", rbase + 27),
            ("25", "ALERT", "RT3", rbase + 28),
            ("31", "DCHG", "RT4", rbase + 29),
            ("28", "HDQ", "RT5", rbase + 30),
        ]
        for idx, (pin, name, rt, rnum) in enumerate(channels):
            net = f"{name}_NTC"
            dx = -18 if bq[pin][0] < ic[0] else 18
            stub(pin, net, dx)
            col_x = 620 + idx * 28
            col_y = 200
            series = sch.part(
                catalog, "Device:R", (col_x, col_y), 0,
                f"R{rnum}", "OPEN", FP_R0603, GEOM["Device:R"], path,
            )
            mark(f"R{rnum}", f"{name} series resistor. Firmware subtracts 500 ohm; the fitted value is OPEN.")
            therm = sch.part(
                catalog, "Device:Thermistor", (col_x, col_y + 20), 0,
                rt, "OPEN", "", GEOM["Device:Thermistor"], path,
            )
            mark(rt, f"{name} NTC. Value and MPN are OPEN. Firmware assumes 10 kOhm, beta 3380, and the internal 18 kOhm pull-up.")
            top = lab(net, (series["1"][0], series["1"][1] - 6), 0, "local")
            sch.wire(top, series["1"])
            sch.wire(series["2"], therm["1"])
            gg = pwr(vss, (therm["2"][0], therm["2"][1] + 6))
            sch.wire(therm["2"], gg)
        vss_pins = ("29", "30", "32")
    else:
        stub("25", "ALERT_BQ2", 22, "hier", "bidirectional")
        vss_pins = ("21", "23", "28", "29", "30", "31", "32")
    for number in vss_pins:
        pt = bq[number]
        dest = (pt[0] - 12, pt[1]) if pt[0] < ic[0] else (pt[0] + 12, pt[1])
        gg = pwr(vss, dest)
        sch.wire(pt, gg)

    # Intentional no-connects.
    for number in ("19", "44", "34", "38", "39", "40", "43", "45"):
        sch.noconn(bq[number])

    domain = "Upper" if upper else "Lower"
    addr = (
        "Upper 7-bit address is 0x08, and only after the lower device has been verified at 0x10. TMUX154E host-side gating is on the isolation sheet."
        if upper
        else "CRC I2C at 100 kHz. SDA is ESP32 GPIO21 and SCL is GPIO20. Startup 7-bit address is 0x08. Firmware then moves this device to 0x10."
    )
    current = (
        "SLUSE13B section 16.6 Table 16-3, pins 18 and 20: If not used, these pins should be connected to pin 17 (VSS). Upper VSS is CELL16. No net here joins lower ground, lower SRP, or lower SRN."
        if upper
        else "SRP and SRN are one Kelvin pair for the charge shunt. Place the 100 ohm / 100 nF filter at the device (SLUSE13B 16.2 and 18.1). Optional 100 pF and 0.1 uF-to-VSS parts are not fitted. Charging current must make SRP positive relative to SRN. CHG- is a sheet port."
    )
    note = "\n".join([
        f"{domain} monitor {ref_ic}, BQ7695202. Local reference and exposed pad are {vss}.",
        "Cell filter copied from SLUSE13B 7.3 and EVM guide section 5.4 Figure 5-9:",
        "20 ohm in series with each VC pin, 220 nF between adjacent filtered nodes, and 220 nF from the VC0 node to local VSS.",
        "Section 7.3 allows 20-100 ohm and 0.1-1 uF. Cell-resistor footprint and power rating are OPEN.",
        "VC pins are also the internal balance pins (Table 6-1). Host balancing is the firmware mode.",
        "External balance network is OPEN. R_B1-R_B33 stay fixed for the case and are not drawn.",
        "Those 33 resistors are not a 33-cell stack.",
        "BQ7695202 REG1 defaults to 3.3 V (section 5). That default does not replace REG0 or the wake pins.",
        "REG18 capacitor is 2.2 uF, inside the 1.8-22 uF range in section 7.10. REG1 capacitor is 1 uF (section 7.12).",
        "REGIN capacitor is 22 nF (section 7.11, allowed 15-27 nF). CBREG 150 pF is the table maximum, not a fitted part.",
        "BAT 100 ohm, 1 uF, and 100 pF follow Figure 16-2. High-voltage footprints are OPEN.",
        "CP1 is tied to BAT because the charge pump is unused (Table 16-3). Enabling it with that tie adds about 200 uA.",
        "CHG, DSG, PCHG, and PDSG are left floating (Table 16-3). Discharge protection is out of scope.",
        "FUSE and REG2 are left floating (Table 16-3). Pins 19 and 44 are not connected to silicon.",
        "PACK uses 10 kOhm to this monitor's top of stack, the no-high-side-FET connection in section 16.2.",
        "RST_SHUT, TS2, and LD wake sources are sheet ports marked OPEN. Do not put a thermistor on TS2 (section 13.5).",
        "SSZT191: every monitor needs a wake path. TS2 is pulled to this domain's VSS to wake; LD voltage must stay inside section 7.3.",
        addr,
        current,
        "Connector value labels are wrong. These are assigned PCB nets, not harness proof, and no connector is relabeled here.",
        "J_CELL1 pins 1-10 = CELL9 down to CELL0. J_CELL2 pins 1-9 = CELL18 down to CELL10.",
        "J_CELL3 pins 1-8 = CELL26 down to CELL19. J_CELL4 pins 1-6 = CELL32 down to CELL27.",
        "Pin 49 is the exposed pad of footprint TQFP-48-1EP and is tied to the local reference.",
        "SLUSE13B package outline PFB0048A shows no exposed thermal pad. Pad 49 keeps that footprint copper on the local reference.",
        "OPEN parts:",
        *opens,
    ])
    sch.text((20.32, 575), note, 1.05)
    sch.opens = opens
    return sch


def build_iso_sheet(catalog):
    path = f"/{ROOT_UUID}/{ISO_SHEET}"
    sch = Sch(
        ISO_FILE,
        "A3",
        "QFBMS32 upper I2C isolation",
        "GPIO9 is pulled high at reset. GPIO9 low selects ESP32-C3 download mode.",
        "4",
    )
    nref = [501]
    opens = []

    def mark(ref, function):
        opens.append(f"{ref}: {function}")

    def pwr_gnd(net, at):
        return gnd(sch, catalog, net, at, path, nref)

    def pwr_vcc(at):
        pins = sch.part(
            catalog, "power:VCC", at, 0, f"#PWR{nref[0]:04d}", "HOST_3V3", "",
            GEOM["power:VCC"], path, bom=False,
        )
        nref[0] += 1
        return pins["1"]

    iso = sch.part(
        catalog, "qfbms:ISO1640_D8", (165.1, 120), 0, "U_ISO", "OPEN",
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        GEOM["qfbms:ISO1640_D8"], path,
    )
    # Keep reference and unresolved value clear of the isolator signal pins.
    sch.body[-1] = sch.body[-1].replace('(at 169.1 120.88 0)', '(at 165.1 96.52 0)').replace('(at 169.1 117.88 0)', '(at 165.1 100.33 0)')
    mark("U_ISO", "Bidirectional I2C isolator using the ISO1640 8-D pin map (VCC1, SDA1, SCL1, GND1, GND2, SCL2, SDA2, VCC2). No enable pin. Orderable suffix is OPEN; the 16-DW package has different pin numbers and is not this symbol.")
    # Side 1 is the host side. Side 2 is the upper-BQ bus.
    sda1, scl1 = iso["2"], iso["3"]
    gnd1, gnd2 = iso["4"], iso["5"]
    scl2, sda2 = iso["6"], iso["7"]
    vcc1, vcc2 = iso["1"], iso["8"]

    # TI TMUX154E uses its active-low enable directly: GPIO9 high disconnects;
    # GPIO9 low connects the selected A0/B0 pair to the common A/B pair.
    sw = sch.part(
        catalog, "qfbms:TMUX154E", (110, 96.52), 0,
        "U204", "TMUX154EDGSR", FP_VSSOP10,
        GEOM["qfbms:TMUX154E"], path,
    )
    mark("U204", "TI TMUX154EDGSR, 2-channel SPDT switch in VSSOP-10. Pin 4 A and pin 6 B are the host-side SDA/SCL commons; pins 2 A0 and 8 B0 face ISO1640 SDA1/SCL1. Pins 3 A1 and 7 B1 are unused; pin 1 SEL is held low to select A0/B0; pin 9 EN is active low and goes directly to GPIO9; pin 10 VCC is HOST_3V3; pin 5 GND is CELL0. TI specifies 3.0-4.3 V supply, I/O to 5.25 V, and high-impedance I/O when unpowered.")
    for pin, name, direction, kind in (
        ("4", "SDA_HOST", 0, "bidirectional"),
        ("2", "SDA_ISO_SIDE", 180, None),
        ("6", "SCL_HOST", 0, "bidirectional"),
        ("8", "SCL_ISO_SIDE", 180, None),
    ):
        endpoint = (sw[pin][0] + (7.62 if direction == 0 else -7.62), sw[pin][1])
        sch.wire(sw[pin], endpoint)
        if kind:
            sch.label(name, endpoint, direction, "hier", kind)
        else:
            sch.label(name, endpoint, direction)
    sch.noconn(sw["3"])
    sch.noconn(sw["7"])
    pwr_gnd("CELL0", sw["1"])
    sch.label("GPIO9", sw["9"], 0, "hier", "bidirectional")
    sch.label("HOST_3V3", sw["10"], 0)
    pwr_gnd("CELL0", sw["5"])

    # The switch connects both upper pull-ups to lower-side pulls when enabled.
    sch.label("SDA_ISO_SIDE", sda1, 0)
    sch.label("SCL_ISO_SIDE", scl1, 0)

    r_sda = sch.part(
        catalog, "Device:R", (100.33, 146.05), 0,
        "R201", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    r_scl = sch.part(
        catalog, "Device:R", (124.46, 146.05), 0,
        "R202", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark("R201", "Switch/ISO1640 side-1 SDA pull-up to HOST_3V3. Resistance remains OPEN pending rail-difference, aggregate sink-current, capacitance and rise-time calculation at 100 kHz.")
    mark("R202", "Switch/ISO1640 side-1 SCL pull-up to HOST_3V3. Resistance remains OPEN pending rail-difference, aggregate sink-current, capacitance and rise-time calculation at 100 kHz.")
    # Angle 0: pin 2 is above the resistor center, pin 1 is below.
    sch.label("SDA_ISO_SIDE", r_sda["1"], 0)
    sch.label("SCL_ISO_SIDE", r_scl["1"], 0)
    vcc_rail = (r_sda["2"][0] - 12.7, r_sda["2"][1])
    sch.wire(r_sda["2"], r_scl["2"])
    host = pwr_vcc(vcc_rail)
    sch.wire(r_sda["2"], host)
    supply_stub = (vcc1[0], vcc1[1] - 10.16)
    sch.wire(vcc1, supply_stub)
    sch.label("HOST_3V3", supply_stub)
    flag(sch, catalog, (host[0] - 7.62, host[1]), path, nref)
    sch.wire((host[0] - 7.62, host[1]), host)
    host_port = sch.label("HOST_3V3", (host[0] - 20.32, host[1]), 180, "hier", "bidirectional")
    sch.wire(host_port, host)

    # Local supply bypassing for the bus switch.
    for ref, center in (("C203", (93.98, 85.09)),):
        c = sch.part(catalog, "Device:C", center, 0, ref, "100nF", FP_C0603,
                     GEOM["Device:C"], path)
        mark(ref, "100 nF local bypass from HOST_3V3 to CELL0.")
        sch.label("HOST_3V3", c["2"], 0)
        pwr_gnd("CELL0", c["1"])

    c_vcc1 = sch.part(
        catalog, "Device:C", (vcc1[0] - 12.7, vcc1[1]), 0,
        "C201", "100nF", FP_C0603, GEOM["Device:C"], path,
    )
    sch.elbow(c_vcc1["2"], vcc1)
    g1 = pwr_gnd("CELL0", (c_vcc1["1"][0], c_vcc1["1"][1] - 7.62))
    sch.wire(c_vcc1["1"], g1)
    sch.wire(gnd1, (gnd1[0] - 7.62, gnd1[1]))
    g1b = pwr_gnd("CELL0", (gnd1[0] - 12.7, gnd1[1]))
    sch.wire((gnd1[0] - 7.62, gnd1[1]), g1b)

    bq_sda = sch.label("SDA_BQ2", (sda2[0] + 20.32, sda2[1]), 0, "hier", "bidirectional")
    bq_scl = sch.label("SCL_BQ2", (scl2[0] + 20.32, scl2[1]), 0, "hier", "bidirectional")
    sch.wire(sda2, bq_sda)
    sch.wire(scl2, bq_scl)
    reg1 = sch.label("REG1_BQ2", (vcc2[0] + 20.32, vcc2[1]), 0, "hier", "bidirectional")
    sch.wire(vcc2, reg1)
    c_vcc2 = sch.part(
        catalog, "Device:C", (vcc2[0] + 12.7, vcc2[1] - 12.7), 0,
        "C202", "100nF", FP_C0603, GEOM["Device:C"], path,
    )
    sch.elbow(vcc2, c_vcc2["2"])
    g2 = pwr_gnd("CELL16", (c_vcc2["1"][0], c_vcc2["1"][1] - 7.62))
    sch.wire(c_vcc2["1"], g2)
    g2b = pwr_gnd("CELL16", (gnd2[0] + 12.7, gnd2[1]))
    sch.wire(gnd2, g2b)

    alert = sch.label("ALERT_BQ2", (40.64, 40.64), 180, "hier", "bidirectional")
    sch.wire(alert, (55.88, 40.64))
    sch.noconn((55.88, 40.64))
    mark(
        "ALERT_BQ2",
        "Upper ALERT stays on the upper side and ends at a no-connect on this sheet. Do not tie it to CELL0. Firmware does not consume upper ALERT. A unidirectional isolator MPN across the barrier is OPEN; do not invent that part.",
    )
    sch.text((58, 42), "ALERT_BQ2 stops here. Do not tie it to CELL0. A unidirectional isolator MPN is OPEN. Firmware does not consume upper ALERT.", 1.05)

    gpio = sch.label("GPIO9", (40.64, 165.1), 180, "hier", "bidirectional")
    r_gpio = sch.part(
        catalog, "Device:R", (70, 165.1), 90,
        "R203", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark("R203", "GPIO9 reset pull-up to HOST_3V3. Value is OPEN. GPIO9 must be high at reset because GPIO9 low selects ESP32-C3 download mode; that level disables U204.")
    sch.wire(gpio, r_gpio["1"])
    v_gpio = pwr_vcc((r_gpio["2"][0] + 10.16, r_gpio["2"][1]))
    sch.wire(r_gpio["2"], v_gpio)

    sch.text((20.32, 230), "\n".join([
        "Upper I2C isolation. Discharge protection is out of scope. No charge FET, USB, or CAN.",
        "U_ISO is the ISO1640 8-pin D pin map from the ISO1640 datasheet Table 5-1. It has no enable pin.",
        "Side 1 (SDA1/SCL1) faces the host and is limited to 80 pF. Side 2 faces the upper BQ bus and allows 400 pF.",
        "VCC1 is HOST_3V3, 3 V to 5.5 V. VCC2 is upper REG1, 2.25 V to 5.5 V. Each supply gets 100 nF to its own ground (datasheet 9.2.1).",
        "GND1 is CELL0. GND2 is CELL16. Those grounds are not connected.",
        "TMUX154E U204 uses pins 4/2 for SDA host/ISO-side and pins 6/8 for SCL host/ISO-side; pins 3/7 are unused. Pin 1 SEL is low, pin 9 EN is GPIO9, pin 10 VCC is HOST_3V3, pin 5 GND is CELL0.",
        "U204 EN low connects A/B to A0/B0 (SEL low); EN high opens. GPIO9 high therefore opens at reset, GPIO9 low connects after lower address verification. U204 I/O is high impedance when VCC=0.",
        "U204 needs VCC 3.0-4.3 V. Powered I/O must stay within 0..VCC; powered-off I/O is rated to 5.25 V. Rail envelope must be checked against HOST_3V3 and lower REG1.",
        "R201/R202 and lower R20/R21 are pull-ups on opposite sides. Values remain OPEN pending rail-difference current, combined sink current, 80 pF ISO1640 side-1 loading, rise-time and 100 kHz analysis.",
        "Host/lower-REG1 sequencing and lower-BQ back-power behavior remain OPEN. Baseline C enables ESP32 internal I2C pullups on the same lower bus.",
        "Firmware must verify lower BQ at 0x10 before GPIO9 low enables upper 0x08.",
        "Upper SDA/SCL pull-ups already sit on the upper sheet, on REG1_BQ2.",
        "OPEN parts:",
        *opens,
    ]), 1.05)
    sch.opens = opens
    return sch


def build_root(lower_opens, upper_opens, iso_opens):
    sch = Sch(
        ROOT_UUID,
        "A2",
        "QFBMS32 BQ monitor sheets",
        "Schematic increment only. qfbms32.kicad_pcb is not updated from this file.",
        "1",
    )
    def sheet(at, size, sheet_uuid, name, filename, page, pins):
        x, y = snap(at[0]), snap(at[1])
        w, h = snap(size[0]), snap(size[1])
        pin_txt = []
        positions = {}
        for i, entry in enumerate(pins):
            pname, shape = entry[0], entry[1]
            leave_open = entry[2] if len(entry) > 2 else True
            py = snap(y + 7.62 + i * 7.62)
            # Right edge.
            px = snap(x + w)
            positions[pname] = (px, py)
            pin_txt.append(
                f"""		(pin "{pname}" {shape}
			(at {px} {py} 0)
			(uuid "{uid(f"{sheet_uuid}:sheet-pin:{pname}")}")
			(effects
				(font (size 1.27 1.27))
				(justify right)
			)
		)"""
            )
            if leave_open:
                sch.noconn((px, py))
        sch.add(
            f"""	(sheet
		(at {x} {y})
		(size {w} {h})
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke (width 0.1524) (type solid))
		(fill (color 0 0 0 0.0000))
		(uuid "{sheet_uuid}")
		(property "Sheetname" "{name}"
			(at {x} {y + h + 2} 0)
			(effects (font (size 1.524 1.524)) (justify left bottom))
		)
		(property "Sheetfile" "{filename}"
			(at {x} {y - 2} 0)
			(effects (font (size 1.27 1.27)) (justify left top))
		)
{chr(10).join(pin_txt)}
		(instances
			(project "{PROJECT}"
				(path "/{ROOT_UUID}"
					(page "{page}")
				)
			)
		)
	)"""
        )
        return positions

    lower_pins = [
        ("SDA_HOST", "bidirectional", False),
        ("SCL_HOST", "bidirectional", False),
        ("CHG_NEG", "bidirectional", True),
        ("RST_SHUT_BQ1", "bidirectional", True),
        ("TS2_WAKE_BQ1", "bidirectional", True),
        ("LD_WAKE_BQ1", "bidirectional", True),
    ]
    upper_pins = [
        ("SDA_BQ2", "bidirectional", False),
        ("SCL_BQ2", "bidirectional", False),
        ("ALERT_BQ2", "bidirectional", False),
        ("REG1_BQ2", "bidirectional", False),
        ("RST_SHUT_BQ2", "bidirectional", True),
        ("TS2_WAKE_BQ2", "bidirectional", True),
        ("LD_WAKE_BQ2", "bidirectional", True),
    ]
    iso_pins = [
        ("SDA_BQ2", "bidirectional", False),
        ("SCL_BQ2", "bidirectional", False),
        ("ALERT_BQ2", "bidirectional", False),
        ("REG1_BQ2", "bidirectional", False),
        ("SDA_HOST", "bidirectional", False),
        ("SCL_HOST", "bidirectional", False),
        ("GPIO9", "bidirectional", True),
        ("HOST_3V3", "bidirectional", True),
    ]
    lower = sheet((25.4, 292.1), (170.18, 60.96), LOWER_SHEET, "Lower monitor", "qfbms32-bq-lower.kicad_sch", "2", lower_pins)
    upper = sheet((25.4, 190.5), (170.18, 76.2), UPPER_SHEET, "Upper monitor", "qfbms32-bq-upper.kicad_sch", "3", upper_pins)
    iso = sheet((25.4, 40.64), (170.18, 83.82), ISO_SHEET, "Upper I2C isolation", "qfbms32-bq-iso-i2c.kicad_sch", "4", iso_pins)
    bus = 220.98
    for name in ("SDA_HOST", "SCL_HOST"):
        sch.wire(lower[name], (bus, lower[name][1]))
        sch.wire((bus, lower[name][1]), (bus, iso[name][1]))
        sch.wire((bus, iso[name][1]), iso[name])
        bus = snap(bus + 2.54)
    for name in ("SDA_BQ2", "SCL_BQ2", "ALERT_BQ2", "REG1_BQ2"):
        sch.wire(upper[name], (bus, upper[name][1]))
        sch.wire((bus, upper[name][1]), (bus, iso[name][1]))
        sch.wire((bus, iso[name][1]), iso[name])
        bus = snap(bus + 2.54)
    sch.text((280, 50), "\n".join(textwrap.fill(line, width=100) for line in [
        "Host I2C is SDA_HOST and SCL_HOST: GPIO21 and GPIO20, 100 kHz.",
        "GPIO9 is pulled high on the isolation sheet. GPIO9 low selects ESP32-C3 download mode.",
        "Upper-bus disconnect uses U204 TMUX154E; GPIO9 high opens, low connects after the lower address check.",
        "That connection is allowed only after the lower device has been verified at 0x10.",
        "CHG_NEG and the wake ports remain open. No charge FET, USB, or CAN is on these sheets.",
        "CELL0 and CELL16 stay separate. CELL16 is the upper reference, not the lower ground.",
        "Isolation OPEN items:",
        *iso_opens,
    ]), 1.15)
    return sch


def main():
    catalog, bq_pins = load_libs()
    lower = build_monitor_sheet(False, catalog, bq_pins)
    upper = build_monitor_sheet(True, catalog, bq_pins)
    iso = build_iso_sheet(catalog)
    root = build_root(lower.opens, upper.opens, iso.opens)
    (ROOT / "qfbms32-bq-lower.kicad_sch").write_text(lower.finish(), encoding="utf-8", newline="\r\n")
    (ROOT / "qfbms32-bq-upper.kicad_sch").write_text(upper.finish(), encoding="utf-8", newline="\r\n")
    (ROOT / "qfbms32-bq-iso-i2c.kicad_sch").write_text(iso.finish(), encoding="utf-8", newline="\r\n")
    (ROOT / "qfbms32-bq-monitors.kicad_sch").write_text(root.finish(), encoding="utf-8", newline="\r\n")
    print("lower opens", len(lower.opens))
    print("upper opens", len(upper.opens))
    print("iso opens", len(iso.opens))
    for item in lower.opens + upper.opens + iso.opens:
        print(" ", item)


if __name__ == "__main__":
    main()
