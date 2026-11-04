# Generates the QFBMS monitor schematic increment only.
# Does not read or write qfbms32.kicad_pcb, qfbms32.kicad_sch, or qfbms32.kicad_pro.
import os
import json
import math
import re
import uuid
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
        ("passive", "A2", "3", -15.24, 0, 0),
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
        if lib_id in ("Device:R", "Device:C", "Device:Thermistor") and rot == 0:
            ref_at = (at[0] + 7, at[1] - 1.5)
            val_at = (at[0] + 7, at[1] + 1.5)
        if lib_id == "Transistor_BJT:Q_NPN_BCE":
            ref_at = (at[0]+11,at[1]-2)
            val_at = (at[0]+11,at[1]+1)
        if lib_id == "Device:D":
            ref_at = (at[0], at[1] - 3)
            val_at = (at[0], at[1] + 3)
        if ref in ("U204", "U_ISO"):
            ref_at = (at[0], at[1]-21)
            val_at = (at[0], at[1]-18)
        if ref == "U205":
            ref_at = (at[0], at[1]-25)
            val_at = (at[0], at[1]-21)
        elif not bom:
            val_at = (at[0], at[1] + (5 if lib_id == "power:GND" else -5))
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
			(at {ref_at[0]} {ref_at[1]} {rot % 180})
			(effects (font (size 1.27 1.27)))
		)
		(property "Value" "{value}"
			(at {val_at[0]} {val_at[1]} {rot % 180})
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
        if not bom and ref != "U205":
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
		(date "2026-11-04")
		(rev "0.2")
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
        "A2",
        title,
        "Charge-only monitor sheet. Do not import this netlist into qfbms32.kicad_pcb.",
        page,
    )
    nref = [1 if not upper else 301]
    opens = []

    def mark(ref, function):
        opens.append(f"{ref}: {function}")

    ic = (295.91, 128.27)
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
    base_y = 60.96
    step = 12.7
    y_of = {n: round(base_y + (16 - n) * step, 2) for n in range(17)}
    rx = 63.5
    cap_x = 100.33
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
    g_ic = pwr(vss, (ep[0], ep[1] + 7.62))
    sch.wire(vss_pt, g_ic)
    flag_pt = (g_ic[0] + 27.94, g_ic[1])
    flag(sch, catalog, flag_pt, path, nref)
    sch.wire(g_ic, flag_pt)

    # --- supply: BAT, REG0, REG18, REG1, CP1 ---
    stack = f"CELL{cell0 + 16}"
    sx, sy = 50.8, 360.68
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
            catalog, "Device:C", (bat_node[0] + dx, sy + 12), 0,
            f"C{cbase + 17 + i}", val, fp, GEOM["Device:C"], path,
        )
        sch.wire((bat_node[0] + dx, sy), cap["1"])
        if dx:
            sch.wire(bat_node, (bat_node[0] + dx, sy))
        gg = pwr(vss, (cap["2"][0], cap["2"][1] + 6))
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
        catalog, "Device:D", (q["2"][0] - 3.81, q["2"][1] - 12), 180,
        f"D{dbase + 1}", "OPEN", "", GEOM["Device:D"], path,
    )
    mark(f"D{dbase + 1}", "REG0 collector diode. MPN, voltage rating, and footprint are OPEN.")
    sch.wire(d_col["1"], q["2"])
    sch.elbow(stack_pt, d_col["2"], horizontal_first=False)
    breg = lab("BREG", (q["1"][0] - 12, q["1"][1]), 180, "local")
    sch.wire(breg, q["1"])
    r_breg = sch.part(
        catalog, "Device:R", (q["1"][0] - 12, q["1"][1] + 12), 0,
        f"R{rbase + 18}", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 18}", "BREG-to-VSS resistor. SLUSE13B 16.2.2 says a large resistor such as 10 MOhm; the value is not otherwise fixed.")
    sch.wire(breg, r_breg["1"])
    gg = pwr(vss, (r_breg["2"][0], r_breg["2"][1] + 6))
    sch.wire(r_breg["2"], gg)
    regin = lab("REGIN", (q["3"][0] + 12, q["3"][1]), 0, "local")
    sch.wire(q["3"], regin)
    c_regin = sch.part(
        catalog, "Device:C", (q["3"][0] + 12, q["3"][1] + 12), 0,
        f"C{cbase + 19}", "22nF", FP_C0603, GEOM["Device:C"], path,
    )
    sch.wire(regin, c_regin["1"])
    gg = pwr(vss, (c_regin["2"][0], c_regin["2"][1] + 6))
    sch.wire(c_regin["2"], gg)
    stub("37", "BREG", 20.32)
    stub("36", "REGIN", 20.32)

    c_reg18 = sch.part(
        catalog, "Device:C", (154, 328), 0,
        f"C{cbase + 20}", "2.2uF", FP_C0603, GEOM["Device:C"], path,
    )
    reg18 = stub("24", "REG18", 12.7)
    lab("REG18", c_reg18["1"], 180)
    gg = pwr(vss, (c_reg18["2"][0], c_reg18["2"][1] + 6))
    sch.wire(c_reg18["2"], gg)

    c_reg1 = sch.part(
        catalog, "Device:C", (184, 328), 0,
        f"C{cbase + 21}", "1uF", FP_C0603, GEOM["Device:C"], path,
    )
    reg1_net = "REG1_BQ2" if upper else "REG1_BQ1"
    reg1_kind = "hier" if upper else "local"
    reg1 = stub("35", reg1_net, 12.7, reg1_kind, "bidirectional" if upper else "passive")
    lab(reg1_net, c_reg1["1"], 180, reg1_kind, "bidirectional")
    gg = pwr(vss, (c_reg1["2"][0], c_reg1["2"][1] + 6))
    sch.wire(c_reg1["2"], gg)

    # I2C pull-ups on this domain's REG1.
    # Angle 0 places pin 2 above the symbol center and pin 1 below it.
    i2c_x = 247.65
    i2c_y = 344.17
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
        sda_name, scl_name = "SDA_BQ1", "SCL_BQ1"
    sda_h = lab(sda_name, (sda_r["1"][0], sda_r["1"][1] - 7.62), 270, "hier", "bidirectional")
    scl_h = lab(scl_name, (scl_r["1"][0], scl_r["1"][1] - 7.62), 270, "hier", "bidirectional")
    sch.wire(sda_r["1"], sda_h)
    sch.wire(scl_r["1"], scl_h)
    stub("27", sda_name, 25.4, "hier", "bidirectional")
    stub("26", scl_name, 25.4, "hier", "bidirectional")

    # PACK through 10k to local top of stack.
    r_pack = sch.part(
        catalog, "Device:R", (160, 365), 90,
        f"R{rbase + 21}", "10k", "", GEOM["Device:R"], path,
    )
    stub("42", "PACK_PIN", 12.7)
    lab("PACK_PIN", r_pack["1"], 180)
    pack_stack = lab(stack, (r_pack["2"][0] + 12, r_pack["2"][1]), 0, "global")
    sch.wire(r_pack["2"], pack_stack)

    # Wake pins. Upstream sources are sheet ports.
    r_rst = sch.part(
        catalog, "Device:R", (391, 320), 90,
        f"R{rbase + 22}", "OPEN", FP_R0603, GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 22}", "RST_SHUT pulldown to local VSS. SLUSE13B 12.6 requires the pin low in normal operation; the resistor value is not specified. The upstream driver is the sheet port.")

    gg = pwr(vss, (r_rst["1"][0], r_rst["1"][1] + 6))
    sch.wire(r_rst["1"], gg)
    rst_name = "RST_SHUT_BQ2" if upper else "RST_SHUT_BQ1"
    rst_h = lab(rst_name, (bq["33"][0] - 35, bq["33"][1]), 180, "hier", "bidirectional")
    sch.wire(rst_h, bq["33"])
    lab(rst_name, r_rst["2"], 0, "hier", "bidirectional")

    ts2_name = "TS2_WAKE_BQ2" if upper else "TS2_WAKE_BQ1"
    ts2_h = lab(ts2_name, (bq["22"][0] - 20, bq["22"][1]), 180, "hier", "bidirectional")
    sch.wire(bq["22"], ts2_h)

    r_ld = sch.part(
        catalog, "Device:R", (391, 345), 90,
        f"R{rbase + 23}", "OPEN", "", GEOM["Device:R"], path,
    )
    mark(f"R{rbase + 23}", "LD series resistor. Value, MPN, and footprint are OPEN. SSZT191 allows wake from LD only with the voltage limited to the datasheet range versus this domain's VSS.")
    stub("41", "LD_PIN", 12.7)
    lab("LD_PIN", r_ld["1"], 180)
    ld_name = "LD_WAKE_BQ2" if upper else "LD_WAKE_BQ1"
    ld_h = lab(ld_name, (r_ld["2"][0] + 12, r_ld["2"][1]), 0, "hier", "bidirectional")
    sch.wire(r_ld["2"], ld_h)

    # Current inputs.
    if upper:
        common_x = bq["18"][0] - 17.78
        for number in ("18", "20"):
            pt = bq[number]
            sch.wire(pt, (common_x, pt[1]))
        sch.wire((common_x, bq["18"][1]), (common_x, bq["20"][1]))
        ground = pwr(vss, (common_x - 12.7, bq["18"][1]))
        sch.wire((common_x, bq["18"][1]), ground)
    else:
        # One shunt. SRP is the CELL0 end and SRN is the CHG- end.
        shunt = sch.part(
            catalog, "Device:R", (451, 81), 90,
            "R_SH", "OPEN", "", GEOM["Device:R"], path,
        )
        mark("R_SH", "Single charge-current shunt. Value, MPN, and footprint are OPEN. Do not copy the R001 silkscreen and do not put the existing shunt footprints in series.")
        cell0_pt = lab("CELL0", (shunt["1"][0] - 12.7, shunt["1"][1]), 180, "global")
        sch.wire(cell0_pt, shunt["1"])
        chg = lab("CHG_NEG", (shunt["2"][0] + 12.7, shunt["2"][1]), 0, "hier", "bidirectional")
        sch.wire(shunt["2"], chg)
        r_srp = sch.part(
            catalog, "Device:R", (shunt["1"][0]-15.24, shunt["1"][1] + 17.78), 0,
            f"R{rbase + 24}", "100", FP_R0603, GEOM["Device:R"], path,
        )
        r_srn = sch.part(
            catalog, "Device:R", (shunt["2"][0]+15.24, shunt["2"][1] + 17.78), 0,
            f"R{rbase + 25}", "100", FP_R0603, GEOM["Device:R"], path,
        )
        sch.elbow(shunt["1"], r_srp["1"], False)
        sch.elbow(shunt["2"], r_srn["1"], False)
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
            col_x = 390 + idx * 30
            col_y = 225
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
        lab(vss, dest, 180 if pt[0] < ic[0] else 0, "global")
        sch.wire(pt, dest)

    # Intentional no-connects.
    for number in ("19", "44", "34", "38", "39", "40", "43", "45"):
        sch.noconn(bq[number])

    domain = "Upper" if upper else "Lower"
    sch.text((28, 20), f"{domain} monitor   /   cells {cell0+1} to {cell0+16}   /   reference {vss}", 3.5)
    for x, y, title in [(28, 43, "01   Cell input filters"), (222, 60, "02   Monitor pinout"),
                        (30, 282, "05   BAT and local regulators"), (220, 292, "06   I2C pull-ups"),
                        (365, 292, "07   Wake interface")]:
        sch.text((x, y), title, 2)
    sch.text((220, 360), "OPEN   Select pulls at 100 kHz. Check rail limits,\nsink current and rise time for this segment.", 1.5)
    sch.text((365, 360), f"OPEN   TS2 is a {vss}-referenced contact port.\nPull low, then release. REG1 can be off.\nWake source, hot leakage and control are unresolved.", 1.5)
    sch.text((30, 390), "OPEN   Select stack-rated diodes, REG0 transistor and passive ratings. Check REGIN headroom and dissipation.", 1.5)
    sch.text((365, 54), "03   Current sense", 2)
    sch.text((365, 185), "04   Temperature inputs", 2)
    if upper:
        sch.text((365, 68), "SRP (18) and SRN (20) share upper VSS (17).\nThe current shunt is on the lower monitor.", 1.6)
        sch.text((365, 200), "Internal temperature only. Unused sensor inputs return to CELL16.\nALERT terminates on the interface sheet.", 1.6)
    else:
        sch.text((365, 125), "OPEN   Confirm Kelvin pickup, shunt value and firmware sign/gain.", 1.5)
        sch.text((365, 265), "OPEN   Firmware assumes 10 kOhm / beta 3380 and 500 ohm series correction.", 1.5)
        sch.text((220, 204), "OPEN   SDA_BQ1 and SCL_BQ1 stop at the sheet boundary.\nHost power sequencing and bus thresholds are unresolved.", 1.5)
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

    def port(pins, num, net, dx, kind="local"):
        x,y = pins[num]
        end = (x+dx,y)
        sch.wire((x,y),end)
        sch.label(net,end,0 if dx>0 else 180,kind,"bidirectional")

    sch.text((22, 20), "Upper monitor communication", 3.3)
    sch.text((22, 30), "CELL0 host domain", 2)
    sch.text((280, 30), "CELL16 upper domain", 2)
    sch.text((22, 52), "01   GPIO9-controlled disconnect", 2)
    sch.text((201, 52), "02   ISO1640 domain boundary", 2)
    sw = sch.part(catalog, "qfbms:TMUX154E", (91.44, 93.98), 0,
                  "U204", "TMUX154EDGSR", FP_VSSOP10, GEOM["qfbms:TMUX154E"], path)
    for pin, net, dx, kind in [("4","SDA_HOST",12.7,"hier"),("6","SCL_HOST",12.7,"hier"),
                               ("2","SDA_ISO_SIDE",-12.7,"local"),("8","SCL_ISO_SIDE",-12.7,"local")]:
        port(sw,pin,net,dx,kind)
    for num in ("3","7"):
        sch.noconn(sw[num])
    for num in ("1","5"):
        g = pwr_gnd("CELL0",(sw[num][0],sw[num][1]+7.62))
        sch.wire(sw[num],g)
    for num, net, dx, kind in [("9","GPIO9",-10.16,"hier"),("10","HOST_3V3",10.16,"hier")]:
        port(sw,num,net,dx,kind)
    sch.text((22, 128), "GPIO9 high opens both lines. Low selects A0/B0 after the lower address check.",1.4)
    iso = sch.part(catalog,"qfbms:ISO1640_D8",(256.54,93.98),0,"U_ISO","ISO1640",
                   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",GEOM["qfbms:ISO1640_D8"],path)
    for num, net, dx, kind in [("2","SDA_ISO_SIDE",-12.7,"local"),("3","SCL_ISO_SIDE",-12.7,"local"),
                               ("7","SDA_BQ2",12.7,"hier"),("6","SCL_BQ2",12.7,"hier"),
                               ("1","HOST_3V3",-12.7,"hier"),("8","REG1_BQ2",12.7,"hier")]:
        port(iso,num,net,dx,kind)
    for num, net, dx in [("4","CELL0",-12.7),("5","CELL16",12.7)]:
        g = pwr_gnd(net,(iso[num][0]+dx,iso[num][1]))
        sch.wire(iso[num],g)
    sch.text((201,128),"OPEN   Select ISO1640 orderable 8-D suffix. Check rail margins and sequencing.",1.4)
    alert = sch.label("ALERT_BQ2",(332,154),180,"hier","bidirectional")
    end = (alert[0]+10.16,alert[1])
    sch.wire(alert,end)
    sch.noconn(end)
    sch.text((280,163),"Upper ALERT stops here; host firmware does not read it.",1.35)
    sch.text((22,149),"03   Host pull-ups and reset bias",2)
    for i,(ref,net) in enumerate([("R201","SDA_ISO_SIDE"),("R202","SCL_ISO_SIDE"),("R203","GPIO9")]):
        pins = sch.part(catalog,"Device:R",(48+45*i,180),0,ref,"OPEN",FP_R0603,GEOM["Device:R"],path)
        port(pins,"1",net,-5.08,"hier" if i==2 else "local")
        rail = pwr_vcc((pins["2"][0]-12.7,pins["2"][1]+5.08))
        sch.elbow(pins["2"],rail,False)
        if i==0:
            pt=(rail[0]-10.16,rail[1])
            flag(sch,catalog,pt,path,nref)
            sch.wire(pt,rail)
    sch.text((22,206),"OPEN   R201/R202: 4.7 kOhm candidate at 100 kHz. Verify rise time, sink current and 80 pF side-1 limit.\nOPEN   R203: size for reset-high GPIO9 and ESP32-C3 boot strapping.",1.45)
    sch.text((201,187),"04   Local bypass",2)
    for x,ref,rail,ground in [(216,"C203","HOST_3V3","CELL0"),(274,"C201","HOST_3V3","CELL0"),(336,"C202","REG1_BQ2","CELL16")]:
        pins=sch.part(catalog,"Device:C",(x,216),0,ref,"100nF",FP_C0603,GEOM["Device:C"],path)
        port(pins,"2",rail,12.7,"hier")
        g=pwr_gnd(ground,(pins["1"][0]-12.7,pins["1"][1]))
        sch.wire(pins["1"],g)
    sch.opens = opens
    return sch


def build_root():
    sch = Sch(
        ROOT_UUID,
        "A3",
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
            left = sheet_uuid == UPPER_SHEET or (sheet_uuid == ISO_SHEET and i >= 4)
            if sheet_uuid == ISO_SHEET and left:
                py = snap(y + 7.62 + (i - 4) * 7.62)
            px = x if left else snap(x + w)
            positions[pname] = (px, py)
            pin_txt.append(
                f"""		(pin "{pname}" {shape}
			(at {px} {py} {180 if left else 0})
			(uuid "{uid(f"{sheet_uuid}:sheet-pin:{pname}")}")
			(effects
				(font (size 1.27 1.27))
				(justify {"left" if left else "right"})
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
			(at {x} {y - 1} 0)
			(effects (font (size 1.524 1.524)) (justify left bottom))
		)
		(property "Sheetfile" "{filename}"
			(at {x} {y + h + 1} 0)
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
        ("SDA_BQ1", "bidirectional", True),
        ("SCL_BQ1", "bidirectional", True),
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
        ("GPIO9", "bidirectional", False),
        ("HOST_3V3", "bidirectional", False),
    ]
    sch.text((23, 21), "32-cell monitor interface", 4)
    sch.text((23, 32), "Charge-only BMS   /   100 kHz I2C   /   ESP32-C3 host", 2)
    host_at = (53.34, 101.6)
    signals = [("21","SDA","SDA_HOST"), ("20","SCL","SCL_HOST"),
               ("9","GPIO9","GPIO9"), ("3V3","3V3","HOST_3V3")]
    host_pins = {}
    pin_defs = []
    for i,(gpio,name,net) in enumerate(signals):
        y = 11.43 - i * 7.62
        number = str(i + 1)  # Logical interface port, not an ESP32 package pad.
        host_pins[number] = (34.29,y)
        caption = f"GPIO{gpio} / {name}" if i < 2 else name
        pin_defs.append(f'(pin passive line (at 34.29 {y} 180) (length 5.08) '
                        f'(name "{caption}" (effects (font (size 1.524 1.524)))) '
                        f'(number "{number}" (effects (font (size 1 1)))))')
    lib = "qfbms:Host_interface"
    symbol = (f'(symbol "{lib}" (pin_numbers (hide yes)) (in_bom no) (on_board no) '
              '(property "Reference" "U" (at 0 24 0) (effects (font (size 1.5 1.5)))) '
              '(property "Value" "ESP32-C3 interface" (at 0 20 0) (effects (font (size 1.5 1.5)))) '
              '(symbol "Host_interface_0_1" (rectangle (start -27.94 17.78) (end 29.21 -17.78) '
              '(stroke (width 0.25) (type default)) (fill (type background)))) '
              '(symbol "Host_interface_1_1" ' + " ".join(pin_defs) + '))')
    host = sch.part({lib:symbol}, lib, host_at, 0, "U205", "ESP32-C3 interface", "",
                    host_pins, f"/{ROOT_UUID}", False)
    sch.text((25, 128), "External host   /   logical ports", 1.6)
    iso = sheet((152.4, 82.55), (86.36, 45.72), ISO_SHEET, "Upper I2C isolation", "qfbms32-bq-iso-i2c.kicad_sch", "4", iso_pins)
    upper = sheet((305, 82.55), (75, 62), UPPER_SHEET, "Upper monitor", "qfbms32-bq-upper.kicad_sch", "3", upper_pins)
    lower = sheet((23, 172), (66, 52), LOWER_SHEET, "Lower monitor", "qfbms32-bq-lower.kicad_sch", "2", lower_pins)
    for index, (net, pin) in enumerate([("SDA_HOST", "GPIO21"), ("SCL_HOST", "GPIO20"),
                                        ("GPIO9", "GPIO9"), ("HOST_3V3", "3V3")]):
        y = iso[net][1]
        start = host[str(index+1)]
        sch.wire(start, iso[net])
        if index < 2:
            sch.label(net, start)
    for net in ("SDA_BQ2", "SCL_BQ2", "ALERT_BQ2", "REG1_BQ2"):
        sch.wire(iso[net], upper[net])
    sch.text((23, 49), "HOST DOMAIN   /   CELL0", 2)
    sch.text((274, 49), "UPPER DOMAIN   /   CELL16", 2)
    sch.text((155, 56), "U204  TMUX154E   >   U_ISO  ISO1640", 1.8)
    sch.text((155, 64), "Domain boundary inside ISO1640", 1.5)
    sch.text((300, 156), "Cells 17-32   |   upper address 0x08", 1.8)
    sch.text((23, 239), "Cells 1-16   |   lower address 0x08 at reset", 1.8)
    sch.text((145, 175), "Startup sequence", 2.3)
    sch.text((145, 187), "Required after lower interface closure:\n1   GPIO9 high opens U204. Configure the lower address.\n2   Verify lower BQ at 0x10.\n3   Drive GPIO9 low to admit upper BQ at 0x08 through ISO1640.", 1.7)
    sch.text((145, 213), "OPEN   Lower SDA/SCL are disconnected from host.\nTS2 ports require independent wake power and reset-off control.\nUpper TS2 is referenced to CELL16. Do not connect a host GPIO.", 1.6)
    return sch


def main():
    catalog, bq_pins = load_libs()
    lower = build_monitor_sheet(False, catalog, bq_pins)
    upper = build_monitor_sheet(True, catalog, bq_pins)
    iso = build_iso_sheet(catalog)
    root = build_root()
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
