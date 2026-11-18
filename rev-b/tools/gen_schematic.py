"""Generate rev-b/qfbms-rev-b.kicad_sch (flat, label-per-pin) from circuit.PARTS.

Also writes the project-local symbol library, sym/fp lib tables, a minimal
.kicad_pro and bom.csv. Run from anywhere with ordinary Python 3.
"""
import csv
import json
import uuid
from pathlib import Path

import circuit
import symlib
from sexp import Str, dump, kid, kids, parse

HERE = Path(__file__).resolve().parent
REVA = HERE.parent
PROJECT = "qfbms-rev-b"
ROOT_UUID = "cba0ce09-47b5-4490-8952-2db5dd70b492"
NS = uuid.UUID(ROOT_UUID)
LOCAL_LIB = "qfbms_revb"
GRID = 2.54


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(map(str, key))))


def snap(v, g=GRID):
    return round(round(v / g) * g, 4)


# ------------------------------------------------------------ custom symbols
def rect_symbol(name, ref, left, right, bottom=(), top=(), width=15.24, desc=""):
    """Box symbol. Each side: list of (number, name, type[, hidden-stack-of])."""
    rows = max(len(left), len(right), 1)
    h = (rows + 1) * GRID
    w = width
    pins = []

    def add(side, items):
        for i, it in enumerate(items):
            num, nm, typ = it[:3]
            stack = it[3] if len(it) > 3 else []
            if side in ("L", "R"):
                y = h / 2 - GRID * (i + 1)
                x = -w / 2 - GRID if side == "L" else w / 2 + GRID
                ang = 0 if side == "L" else 180
            else:
                x = -w / 2 + GRID * (i + 1)
                y = -h / 2 - GRID if side == "B" else h / 2 + GRID
                ang = 90 if side == "B" else 270
            for j, n in enumerate([num] + list(stack)):
                hidden = j > 0
                t = typ if j == 0 else "passive"
                pins.append(["pin", t, "line", ["at", round(x, 2), round(y, 2), ang], ["length", GRID]]
                            + ([["hide", "yes"]] if hidden else [])
                            + [["name", Str(nm), ["effects", ["font", ["size", 1.27, 1.27]]]],
                               ["number", Str(n), ["effects", ["font", ["size", 1.27, 1.27]]]]])

    add("L", left)
    add("R", right)
    add("B", bottom)
    add("T", top)
    prop = lambda k, v, y, hide=False: (["property", Str(k), Str(v), ["at", 0, y, 0],
                                         ["effects", ["font", ["size", 1.27, 1.27]]]
                                         + ([["hide", "yes"]] if hide else [])])
    return ["symbol", Str(name), ["pin_names", ["offset", 1.016]], ["exclude_from_sim", "no"],
            ["in_bom", "yes"], ["on_board", "yes"],
            prop("Reference", ref, h / 2 + 5), prop("Value", name, -h / 2 - 5),
            prop("Footprint", "", 0, True), prop("Datasheet", "", 0, True),
            prop("Description", desc, 0, True),
            ["symbol", Str(f"{name}_0_1"),
             ["rectangle", ["start", -w / 2, h / 2], ["end", w / 2, -h / 2],
              ["stroke", ["width", 0.254], ["type", "default"]], ["fill", ["type", "background"]]]],
            ["symbol", Str(f"{name}_1_1")] + pins]


def custom_lib():
    gnd_stack = ["2", "11", "14"] + [str(n) for n in range(36, 54)]
    esp = rect_symbol(
        "ESP32-C3-MINI-1", "U",
        left=[("3", "3V3", "power_in"), ("8", "EN", "input"), ("12", "IO0", "bidirectional"),
              ("13", "IO1", "bidirectional"), ("5", "IO2", "bidirectional"),
              ("6", "IO3", "bidirectional"), ("18", "IO4", "bidirectional"),
              ("19", "IO5", "bidirectional"), ("16", "IO10", "bidirectional")],
        right=[("20", "IO6", "bidirectional"), ("21", "IO7", "bidirectional"),
               ("22", "IO8", "bidirectional"), ("23", "IO9", "bidirectional"),
               ("26", "IO18/USB_D-", "bidirectional"), ("27", "IO19/USB_D+", "bidirectional"),
               ("30", "RXD0/IO20", "bidirectional"), ("31", "TXD0/IO21", "bidirectional")],
        bottom=[("1", "GND", "power_in", gnd_stack)], width=25.4,
        desc="ESP32-C3-MINI-1 module. Pin numbers from Espressif datasheet v2.2 Table 3-1. "
             "NC pins 4,7,9,10,15,17,24,25,28,29,32-35 omitted.")
    vom = rect_symbol(
        "VOM1271", "U",
        left=[("1", "LED_A", "passive"), ("2", "LED_K", "passive")],
        right=[("4", "VO+", "passive"), ("3", "VO-", "passive")], width=10.16,
        desc="Vishay VOM1271 photovoltaic MOSFET driver, SOP-4. Pin 4 positive, pin 3 negative per Vishay 83469 Fig 9.")
    watchdog = rect_symbol("TPS3431", "U",
        left=[("1", "VDD", "power_in"), ("2", "CWD", "input"), ("3", "EN", "input"), ("5", "SET1", "input"), ("6", "WDI", "input")],
        right=[("7", "~{WDO}", "open_collector"), ("8", "ENOUT", "open_collector")],
        bottom=[("4", "GND", "power_in"), ("9", "EP", "passive")],
        desc="TI TPS3431 SNVSB66A table 5-1; footprint EP mapped to pad 9")
    latch = rect_symbol("SN74LVC1G74", "U",
        left=[("1", "CLK", "input"), ("2", "D", "input"), ("6", "~{CLR}", "input"), ("7", "~{PRE}", "input")],
        right=[("5", "Q", "output"), ("3", "~{Q}", "output")],
        top=[("8", "VCC", "power_in")], bottom=[("4", "GND", "power_in")],
        desc="TI SN74LVC1G74 DCU, SCES794G table 5; Q=5, /Q=3")
    lib = ["kicad_symbol_lib", ["version", 20251024], ["generator", Str("qfbms_revb_gen")],
           ["generator_version", Str("10.0")], esp, vom, watchdog, latch]
    return lib


# ------------------------------------------------------------ geometry
def outward(angle):
    """Pin `angle` points from the connection point into the body (lib, y-up).
    Return the outward unit vector on the sheet (y-down)."""
    return {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[angle]


def sheet_pt(origin, p):
    return (round(origin[0] + p["x"], 4), round(origin[1] - p["y"], 4))


def label_len(net):
    return 1.0 * len(net) + 2.0


def extent(sym, pinlist, nets):
    """Bounding box in sheet coordinates relative to origin, including labels."""
    x0, y0, x1, y1 = symlib.body_box(sym)
    bx0, bx1, by0, by1 = x0, x1, -y1, -y0
    for p in pinlist:
        px, py = p["x"], -p["y"]
        dx, dy = outward(p["angle"])
        reach = GRID + label_len(nets.get(p["number"], "")) if p["number"] in nets else 3
        ex, ey = px + dx * reach, py + dy * reach
        bx0, bx1 = min(bx0, px, ex), max(bx1, px, ex)
        by0, by1 = min(by0, py, ey), max(by1, py, ey)
    return bx0 - 2, by0 - 6, bx1 + 2, by1 + 6


# ------------------------------------------------------------ build
def build():
    symlib.register_local(LOCAL_LIB, [x for x in custom_lib()])
    blocks = ["cells", "lower", "upper", "charge", "power", "mcu", "comms"]
    titles = {"cells": "Cell taps: plugs, R_B1-R_B33 input resistors, filter capacitors",
              "lower": "Lower monitor U_BQ1 (cells 1-16, reference GND) + current sense + temperatures",
              "upper": "Upper monitor U_BQ2 (cells 17-32, reference CELL16)",
              "charge": "Charge path: back-to-back FETs, photovoltaic gate drive, shunt, dividers",
              "power": "Power: 140 V buck to 5 V, USB OR-ing, 3.3 V LDO",
              "mcu": "ESP32-C3 (VBMS32 firmware pins), USB, wake button, buzzer",
              "comms": "Upper-monitor I2C link (bus switch + ISO1640 + switched supply) and isolated CAN"}
    lib_syms = {}
    placed = []
    errors = []
    pin_types = {}  # net -> list of types
    col_w = 330.0
    y_cursor = {}
    block_origin = {}
    # two columns of blocks
    layout = [("cells", 0), ("lower", 0), ("upper", 0), ("charge", 1), ("power", 1), ("mcu", 1), ("comms", 1)]
    col_y = [20.0, 20.0]
    items = []  # schematic body s-exprs
    for blk, col in layout:
        parts = [p for p in circuit.PARTS if p["block"] == blk]
        x_left = 15 + col * (col_w + 20)
        y = col_y[col] + 8
        items.append(["text", Str(titles[blk]), ["exclude_from_sim", "no"],
                      ["at", snap(x_left), snap(y), 0],
                      ["effects", ["font", ["size", 3, 3], ["bold", "yes"]], ["justify", "left"]],
                      ["uuid", uid("title", blk)]])
        y += 10
        cx, row_h = x_left, 0.0
        for p in parts:
            sym = symlib.flatten(p["lib"])
            lib_syms[p["lib"]] = sym
            plist, units = symlib.pins(sym)
            if len(units) > 1:
                errors.append(f"{p['ref']}: multi-unit symbol {p['lib']}")
            nets = dict(p["pins"])
            # stacked pins inherit the net of the pin they sit on
            bypos = {}
            for q in plist:
                bypos.setdefault((q["x"], q["y"]), []).append(q)
            for group in bypos.values():
                named = {nets[q["number"]] for q in group if q["number"] in nets}
                if len(named) > 1:
                    errors.append(f"{p['ref']}: stacked pins on different nets {named}")
                if named:
                    for q in group:
                        nets.setdefault(q["number"], next(iter(named)))
            numbers = {q["number"] for q in plist}
            for n in list(p["pins"]) + p["nc"]:
                if n not in numbers:
                    errors.append(f"{p['ref']}: pin {n} not in symbol {p['lib']}")
            missing = numbers - set(nets) - set(p["nc"])
            if missing:
                errors.append(f"{p['ref']}: pins neither connected nor NC: {sorted(missing)}")
            bx0, by0, bx1, by1 = extent(sym, plist, nets)
            w, h = bx1 - bx0, by1 - by0
            if cx + w > x_left + col_w and cx > x_left:
                cx, y = x_left, y + row_h
                row_h = 0.0
            origin = (snap(cx - bx0), snap(y - by0))
            cx += w + 2
            row_h = max(row_h, h + 2)
            placed.append((p, sym, plist, nets, origin))
        col_y[col] = y + row_h + 15
    # symbols
    for p, sym, plist, nets, origin in placed:
        ref = p["ref"]
        fp = p["fp"] or next(x[2] for x in kids(sym, "property") if x[1] == "Footprint")
        p["fp_resolved"] = fp
        x0, y0, x1, y1 = symlib.body_box(sym)
        prop = lambda k, v, at, hide: (["property", Str(k), Str(v), ["at", at[0], at[1], 0],
                                        ["effects", ["font", ["size", 1.27, 1.27]]]
                                        + ([["hide", "yes"]] if hide else [])])
        nobom = p["lib"] in ("Device:NetTie_2", "Connector:TestPoint", "Jumper:SolderJumper_2_Open")
        body = ["symbol", ["lib_id", Str(p["lib"])], ["at", origin[0], origin[1], 0], ["unit", 1],
                ["body_style", 1], ["exclude_from_sim", "no"], ["in_bom", "no" if nobom else "yes"],
                ["on_board", "yes"],
                ["in_pos_files", "yes"], ["dnp", "no"], ["uuid", uid("sym", ref)],
                prop("Reference", ref, (origin[0], round(origin[1] - y1 - 2.5, 2)), False),
                prop("Value", p["value"], (origin[0], round(origin[1] - y0 + 2.5, 2)), False),
                prop("Footprint", fp, origin, True),
                prop("Datasheet", "", origin, True),
                prop("Description", "", origin, True),
                prop("Purpose", p["purpose"], origin, True),
                prop("MPN", p["mpn"], origin, True)]
        for q in plist:
            body.append(["pin", Str(q["number"]), ["uuid", uid("pin", ref, q["number"])]])
        body.append(["instances", ["project", Str(PROJECT),
                                   ["path", Str("/" + ROOT_UUID), ["reference", Str(ref)], ["unit", 1]]]])
        items.append(body)
        done = set()
        for q in plist:
            pt = sheet_pt(origin, q)
            if pt in done:
                continue
            done.add(pt)
            num = q["number"]
            if num in nets:
                net = nets[num]
                pin_types.setdefault(net, []).append(q["type"])
                dx, dy = outward(q["angle"])
                end = (round(pt[0] + dx * GRID, 4), round(pt[1] + dy * GRID, 4))
                items.append(["wire", ["pts", ["xy", pt[0], pt[1]], ["xy", end[0], end[1]]],
                              ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid("w", ref, num)]])
                ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
                just = "left" if ang in (0, 90) else "right"
                items.append(["label", Str(net), ["at", end[0], end[1], ang],
                              ["effects", ["font", ["size", 1.27, 1.27]], ["justify", just]],
                              ["uuid", uid("l", ref, num)]])
            else:
                items.append(["no_connect", ["at", pt[0], pt[1]], ["uuid", uid("nc", ref, num)]])
    # also count stacked-pin types for nets (types of hidden stacked pins)
    for p, sym, plist, nets, origin in placed:
        for q in plist:
            if q["number"] in nets and q["hidden"]:
                pin_types.setdefault(nets[q["number"]], []).append(q["type"])
    # power flags where a net has power inputs but no power output
    flag_sym = symlib.flatten("power:PWR_FLAG")
    lib_syms["power:PWR_FLAG"] = flag_sym
    need = sorted(n for n, t in pin_types.items() if "power_in" in t and "power_out" not in t)
    fx, fy = 15.0, max(col_y) + 10
    items.append(["text", Str("Power flags (nets fed only by passive parts or connectors)"),
                  ["exclude_from_sim", "no"], ["at", fx, fy, 0],
                  ["effects", ["font", ["size", 3, 3], ["bold", "yes"]], ["justify", "left"]],
                  ["uuid", uid("title", "flags")]])
    for i, net in enumerate(need):
        ox, oy = snap(fx + 10 + (i % 10) * 30), snap(fy + 15 + (i // 10) * 20)
        ref = f"#FLG{i + 1:02d}"
        items.append(["symbol", ["lib_id", Str("power:PWR_FLAG")], ["at", ox, oy, 0], ["unit", 1],
                      ["body_style", 1], ["exclude_from_sim", "no"], ["in_bom", "no"], ["on_board", "no"],
                      ["in_pos_files", "no"], ["dnp", "no"], ["uuid", uid("flag", net)],
                      ["property", Str("Reference"), Str(ref), ["at", ox, oy - 4, 0],
                       ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]],
                      ["property", Str("Value"), Str("PWR_FLAG"), ["at", ox, oy - 4, 0],
                       ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]],
                      ["property", Str("Footprint"), Str(""), ["at", ox, oy, 0],
                       ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]],
                      ["property", Str("Datasheet"), Str("~"), ["at", ox, oy, 0],
                       ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]],
                      ["pin", Str("1"), ["uuid", uid("flagpin", net)]],
                      ["instances", ["project", Str(PROJECT),
                                     ["path", Str("/" + ROOT_UUID), ["reference", Str(ref)], ["unit", 1]]]]])
        end = (ox, round(oy + GRID, 4))
        items.append(["wire", ["pts", ["xy", ox, oy], ["xy", end[0], end[1]]],
                      ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid("fw", net)]])
        items.append(["label", Str(net), ["at", end[0], end[1], 270],
                      ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "right"]],
                      ["uuid", uid("fl", net)]])
    width = snap(2 * col_w + 60, 10)
    height = snap(fy + 25 + (len(need) // 10 + 1) * 20, 10)
    sch = ["kicad_sch", ["version", 20260101], ["generator", Str("eeschema")],
           ["generator_version", Str("10.0")], ["uuid", Str(ROOT_UUID)],
           ["paper", Str("User"), width, height],
           ["title_block", ["title", Str("QFBMS rev B DRAFT - NOT FOR FABRICATION")],
            ["date", Str("2026-11-17")], ["rev", Str("B-draft")],
            ["comment", 1, Str("Generated by rev-b/tools/gen_schematic.py from circuit.py. Do not edit by hand.")],
            ["comment", 2, Str("Every part carries a Purpose field; see rev-b/bom.csv.")]],
           ["lib_symbols"] + list(lib_syms.values())] + items + [
        ["sheet_instances", ["path", Str("/"), ["page", Str("1")]]], ["embedded_fonts", "no"]]
    return sch, errors, need


def write_aux():
    (REVA / f"{LOCAL_LIB}.kicad_sym").write_text(dump(custom_lib()) + "\n", encoding="utf-8")
    (REVA / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n  (lib (name "qfbms_revb")(type "KiCad")'
        '(uri "${KIPRJMOD}/qfbms_revb.kicad_sym")(options "")(descr "Rev B local symbols"))\n)\n',
        encoding="utf-8")
    (REVA / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n  (lib (name "qfbms_revb")(type "KiCad")'
        '(uri "${KIPRJMOD}/qfbms_revb.pretty")(options "")(descr "Rev B local footprints"))\n)\n',
        encoding="utf-8")
    pro = REVA / f"{PROJECT}.kicad_pro"
    if not pro.exists():
        pro.write_text(json.dumps({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
                                   "board": {}, "schematic": {}, "sheets": [[ROOT_UUID, "Root"]]},
                                  indent=2), encoding="utf-8")


def write_bom():
    with open(REVA / "bom.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Block", "Value", "MPN / requirement", "Footprint", "Fixed", "Purpose"])
        for p in circuit.PARTS:
            w.writerow([p["ref"], p["block"], p["value"], p["mpn"], p.get("fp_resolved") or p["fp"],
                        "yes" if p["fixed"] else "", p["purpose"]])


def main():
    refs = [p["ref"] for p in circuit.PARTS]
    dup = {r for r in refs if refs.count(r) > 1}
    if dup:
        raise SystemExit(f"duplicate refs: {sorted(dup)}")
    missing_purpose = [p["ref"] for p in circuit.PARTS if not p["purpose"].strip()]
    if missing_purpose:
        raise SystemExit(f"parts without a purpose: {missing_purpose}")
    sch, errors, flags = build()
    if errors:
        raise SystemExit("\n".join(errors))
    write_aux()
    (REVA / f"{PROJECT}.kicad_sch").write_text(dump(sch) + "\n", encoding="utf-8")
    write_bom()
    print(f"{len(circuit.PARTS)} parts, {len(flags)} power flags: {', '.join(flags)}")


if __name__ == "__main__":
    main()
