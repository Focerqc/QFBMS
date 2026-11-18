"""Build and place rev-a/qfbms-rev-a.kicad_pcb with KiCad 10's Python.

Reads qfbms32.kicad_pcb read-only and never writes it. Keeps the board outline and the
fixed parts (connectors and R_B1-R_B33) at their exact positions and drops everything else.
Loads each rev A footprint, sets nets from the kicad-cli netlist (names exactly as in the
schematic), then places parts:

  1. Anchors: big parts at hand-picked spots (ANCHORS).
  2. The rest, most-connected first: nearest free spot to the pads it connects to, inside
     its voltage domain's region (REGION_OF), trying 4 rotations.

Nothing is routed here; route_board.py does that.

Run: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import circuit  # noqa: E402

REVA = Path(__file__).resolve().parents[1]
ROOT = REVA.parent
OLD = ROOT / "qfbms32.kicad_pcb"
NEW = REVA / "qfbms-rev-a.kicad_pcb"
SCH = REVA / "qfbms-rev-a.kicad_sch"
CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
FPDIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
MM = pcbnew.FromMM
GAP = 0.15          # extra space between courtyards, leaves room for escape routing
EDGE = 0.5

# (x, y, rotation) in board mm. Drain tabs of Q1/Q2 face the XT30 pads.
ANCHORS = {
    "Q2": (23.2, 6.6, 180), "Q1": (22.15, 19.5, 180),
    "U_BQ2": (48.0, 11.5, 0), "U_BQ1": (88.0, 11.5, 0),
    "U_ESP1": (108.4, 8.6, 0),
    "U11": (60.8, 11.5, 180),       # ISO1640: side 2 (pins 5-8) faces the upper monitor
    "U7": (35.5, 13.0, 90),         # ISO1050 beside J_COMM1
    "U4": (69.0, 5.0, 0), "L1": (76.3, 5.0, 0),
    "U12": (60.8, 6.8, 0), "C3": (67.0, 10.9, 0), "C4": (72.0, 10.9, 0), "D2": (76.4, 12.9, 90),  # buck hot loop
    "F1": (20.0, 28.6, 0), "R_SH1": (29.6, 28.6, 0),
}

# Regions per voltage domain (x0, y0, x1, y1). Upper-domain parts stay between x 39 and 63.
R_CHARGE = [(14.6, 0.4, 41.0, 20.4), (14.6, 25.4, 35.4, 31.7)]
R_UPPER = [(41.0, 0.4, 63.2, 20.4)]
R_POWER = [(63.6, 0.4, 82.0, 20.4)]
R_LOWER = [(74.0, 0.4, 101.6, 20.4)]
R_MCU = [(99.4, 0.4, 129.6, 20.4), (102.6, 25.4, 129.6, 31.7)]
R_CAN = [(27.0, 0.4, 41.0, 20.4), (14.6, 25.4, 35.4, 31.7)]
R_BOUNDARY = [(56.0, 0.4, 70.0, 20.4)]

UPPER_EXTRA = {"Q6", "R26", "R27", "R29", "C14"}
BOUNDARY = {"U12", "R28"}
GND_COMMS = {"U9", "U10", "R22", "R23", "R24", "R25", "C11", "C12", "C13"}
CAN = {"U7", "C15", "C16", "R30", "R31", "JP1"}
NEAR_MCU = {"R6", "R8", "C1", "C2"}
IGNORE_FOR_AFFINITY = {"/GND", "/3V3", "/5V", "/CELL16"}


def region_of(p):
    ref, blk = p["ref"], p["block"]
    if ref.startswith("C_F"):
        return R_LOWER if int(ref[3:]) <= 16 else R_UPPER
    if ref in UPPER_EXTRA:
        return R_UPPER
    if ref in BOUNDARY:
        return R_BOUNDARY
    if ref in CAN:
        return R_CAN
    if ref in GND_COMMS:
        return R_POWER + R_LOWER
    if ref in NEAR_MCU:
        return R_MCU
    if ref in ("NT1", "NT2"):
        return R_CHARGE
    return {"charge": R_CHARGE, "upper": R_UPPER, "lower": R_LOWER, "power": R_POWER,
            "mcu": R_MCU, "comms": R_POWER}[blk]


def netlist():
    out = Path(tempfile.mkdtemp()) / "n.xml"
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(SCH)],
                   check=True, capture_output=True)
    pin_net = {}
    for n in ET.parse(out).getroot().iter("net"):
        for nd in n.iter("node"):
            pin_net[(nd.get("ref"), nd.get("pin"))] = n.get("name")
    return pin_net


def lib_path(nick):
    if nick == "qfbms_reva":
        return str(REVA / "qfbms_reva.pretty")
    return str(FPDIR / f"{nick}.pretty")


def bbox_mm(fp):
    b = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()),
            pcbnew.ToMM(b.GetX() + b.GetWidth()), pcbnew.ToMM(b.GetY() + b.GetHeight()))


def court(fp, layer=None):
    layer = pcbnew.F_CrtYd if layer is None else layer
    fp.BuildCourtyardCaches()
    c = fp.GetCourtyard(layer)
    if c.OutlineCount():
        b = c.BBox()
        return (pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()),
                pcbnew.ToMM(b.GetX() + b.GetWidth()), pcbnew.ToMM(b.GetY() + b.GetHeight()))
    b = bbox_mm(fp)
    return (b[0] - 0.3, b[1] - 0.3, b[2] + 0.3, b[3] + 0.3)


def overlaps(a, b, gap=GAP):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def clean_text(path, text, keep_refs):
    """Write `text` to `path` without tracks, zones, non-outline graphics and unkept footprints."""
    out, i, n = [], 0, len(text)
    while i < n:
        line_end = text.find("\n", i)
        line_end = n if line_end < 0 else line_end + 1
        line = text[i:line_end]
        top = line.startswith("\t(") and not line.startswith("\t\t")
        kind = line.lstrip("\t")[1:].split(None, 1)[0].rstrip(")") if top else ""
        if top and (kind in ("segment", "via", "arc", "zone", "footprint") or kind.startswith("gr_")):
            depth, j, instr = 0, i, False
            while j < n:
                c = text[j]
                if instr:
                    if c == "\\":
                        j += 1
                    elif c == '"':
                        instr = False
                elif c == '"':
                    instr = True
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            nl = text.find("\n", j)
            end = n if nl < 0 else nl + 1
            block = text[i:end]
            keep = False
            if kind.startswith("gr_"):
                keep = '(layer "Edge.Cuts")' in block
            elif kind == "footprint":
                m = re.search(r'\(property "Reference" "([^"]+)"', block)
                keep = bool(m and m.group(1) in keep_refs)
            if keep:
                out.append(block)
            i = end
            continue
        out.append(line)
        i = line_end
    path.write_text("".join(out), encoding="utf-8")


def snapshot(board, refs):
    out = {}
    for fp in list(board.GetFootprints()):
        ref = fp.GetReference()
        if ref in refs:
            out[ref] = (round(pcbnew.ToMM(fp.GetPosition().x), 4), round(pcbnew.ToMM(fp.GetPosition().y), 4),
                        fp.GetOrientationDegrees(), fp.IsFlipped(),
                        sorted((p.GetNumber(), round(pcbnew.ToMM(p.GetPosition().x), 4),
                                round(pcbnew.ToMM(p.GetPosition().y), 4),
                                round(pcbnew.ToMM(p.GetSize(pcbnew.F_Cu).x), 4),
                                round(pcbnew.ToMM(p.GetSize(pcbnew.F_Cu).y), 4)) for p in fp.Pads()))
    return out


def main():
    fixed = {p["ref"] for p in circuit.PARTS if p["fixed"]}
    before = snapshot(pcbnew.LoadBoard(str(OLD)), fixed)
    if fixed - set(before):
        raise SystemExit(f"fixed parts not on the old board: {sorted(fixed - set(before))}")
    clean_text(NEW, OLD.read_text(encoding="utf-8"), fixed)
    board = pcbnew.LoadBoard(str(NEW))
    board.SetCopperLayerCount(4)
    pin_net = netlist()
    nets = {}

    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        return nets[name]

    spec = {p["ref"]: p for p in circuit.PARTS}
    fps = {}
    for fp in list(board.GetFootprints()):
        ref = fp.GetReference()
        nick, name = spec[ref]["fp"].split(":")
        fp.SetFPID(pcbnew.LIB_ID(nick, name))
        fp.SetValue(spec[ref]["value"])
        fps[ref] = fp
    for p in circuit.PARTS:
        if p["fixed"]:
            continue
        fpname = p["fp"] or {"U4": "Package_SO:Analog_MSOP-12-16-1EP_3x4.039mm_P0.5mm_EP1.651x2.845mm",
                             "U7": "Package_SO:SOP-8_6.62x9.15mm_P2.54mm"}[p["ref"]]
        p["fp"] = fpname
        nick, name = fpname.split(":")
        fp = pcbnew.FootprintLoad(lib_path(nick), name)
        if fp is None:
            raise SystemExit(f"footprint not found: {fpname}")
        fp.SetFPID(pcbnew.LIB_ID(nick, name))
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        board.Add(fp)
        fps[p["ref"]] = fp
    for ref, fp in fps.items():
        for pad in fp.Pads():
            n = pin_net.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(net(n))
            else:
                pad.SetNetCode(0)
        fp.SetField("Purpose", spec[ref]["purpose"])
        fp.SetField("MPN", spec[ref]["mpn"])
        for fname in ("Purpose", "MPN"):
            f = fp.GetField(fname)
            f.SetLayer(pcbnew.F_Fab)
            f.SetVisible(False)

    ob = board.GetBoardEdgesBoundingBox()
    ox0, oy0 = pcbnew.ToMM(ob.GetX()), pcbnew.ToMM(ob.GetY())
    ox1, oy1 = ox0 + pcbnew.ToMM(ob.GetWidth()), oy0 + pcbnew.ToMM(ob.GetHeight())

    obstacles = {r: court(fps[r]) for r in fixed}
    placed = set(fixed)
    for ref, (x, y, rot) in ANCHORS.items():
        fp = fps[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        obstacles[ref] = court(fp)
        placed.add(ref)
    clash = [(a, b) for a in ANCHORS for b in obstacles if a != b and overlaps(obstacles[a], obstacles[b], 0)]
    if clash:
        print("anchor overlaps:", clash)

    # connectivity
    pad_nets = {ref: {pad.GetNumber(): pad.GetNetname() for pad in fp.Pads() if pad.GetNetname()}
                for ref, fp in fps.items()}
    members = defaultdict(set)
    for ref, d in pad_nets.items():
        for n in d.values():
            members[n].add(ref)

    def pad_pos(ref):
        return {pad.GetNumber(): (pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y))
                for pad in fps[ref].Pads()}

    def links(ref):
        out = []
        for num, n in pad_nets[ref].items():
            if n in IGNORE_FOR_AFFINITY or len(members[n]) > 12:
                continue
            for other in members[n]:
                if other != ref and other in placed:
                    for onum, on in pad_nets[other].items():
                        if on == n:
                            out.append((num, pad_pos(other)[onum]))
        return out

    def free(box, regions, gap):
        if box[0] < ox0 + EDGE or box[1] < oy0 + EDGE or box[2] > ox1 - EDGE or box[3] > oy1 - EDGE:
            return False
        if not any(box[0] >= r[0] and box[1] >= r[1] and box[2] <= r[2] and box[3] <= r[3] for r in regions):
            return False
        return not any(overlaps(box, o, gap) for o in obstacles.values())

    def fallback(ref):
        p = spec[ref]
        if ref in BOUNDARY:
            return R_BOUNDARY + R_UPPER + R_POWER
        upper = p["block"] == "upper" or ref in UPPER_EXTRA or (ref.startswith("C_F") and int(ref[3:]) > 16)
        if upper:
            return R_UPPER + [(37.5, 29.85, 68.5, 31.7)]
        return [(14.6, 0.4, 41.0, 20.4), (14.6, 25.4, 35.4, 31.7), (63.6, 0.4, 129.6, 20.4),
                (68.6, 29.85, 101.6, 31.7), (102.6, 25.4, 129.6, 31.7)]

    unplaced = [p["ref"] for p in circuit.PARTS if p["ref"] not in placed]
    failed = []
    retry = []
    while unplaced or retry:
        second = not unplaced
        if second:
            unplaced, retry = retry, []
        unplaced.sort(key=lambda r: (-len(links(r)), -((lambda b: (b[2] - b[0]) * (b[3] - b[1]))(court(fps[r])))))
        ref = unplaced.pop(0)
        fp = fps[ref]
        regions = fallback(ref) if second else region_of(spec[ref])
        gap = 0.05 if second else GAP
        lk = links(ref)
        if lk:
            tx = sum(p[0] for _, p in lk) / len(lk)
            ty = sum(p[1] for _, p in lk) / len(lk)
        else:
            r0 = regions[0]
            tx, ty = (r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2
        shapes = []
        for rot in (0, 90, 180, 270):
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(pcbnew.VECTOR2I(0, 0))
            b = court(fp)
            pads = {pad.GetNumber(): (pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y))
                    for pad in fp.Pads()}
            shapes.append((rot, b, pads))
        best = None
        step = 0.25
        for ring in range(0, 400):
            r = ring * step
            pts = [(tx, ty)] if ring == 0 else []
            if ring:
                k = int(8 * r / step)
                pts = [(tx + r * math.cos(2 * math.pi * i / k), ty + r * math.sin(2 * math.pi * i / k))
                       for i in range(k)]
            for (x, y) in pts:
                for rot, b, pads in shapes:
                    box = (b[0] + x, b[1] + y, b[2] + x, b[3] + y)
                    if not free(box, regions, gap):
                        continue
                    cost = sum(math.hypot(pads[num][0] + x - px, pads[num][1] + y - py)
                               for num, (px, py) in lk if num in pads)
                    if best is None or cost < best[0]:
                        best = (cost, x, y, rot, box)
            if best and ring * step > (best[0] / max(len(lk), 1)) + 1.0:
                break
            if best and not lk:
                break
        if not best and not second:
            retry.append(ref)
            continue
        if not best:
            failed.append(ref)
            fp.SetPosition(pcbnew.VECTOR2I(MM(ox1 + 10), MM(oy0 + 5 * len(failed))))
            placed.add(ref)
            continue
        _, x, y, rot, box = best
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        obstacles[ref] = box
        placed.add(ref)

    pcbnew.SaveBoard(str(NEW), board)
    check = pcbnew.LoadBoard(str(NEW))
    after = snapshot(check, fixed)
    report = {
        "fixed_checked": len(before),
        "fixed_moved": sorted(r for r in before if after.get(r) != before[r]),
        "footprints": len(list(check.GetFootprints())),
        "unplaced": failed,
        "anchor_overlaps": clash,
    }
    (REVA / "board-build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
