"""Close the connections Freerouting left open, by trial and DRC.

For every unconnected pair that kicad-cli DRC reports (zones refilled), try candidate stubs in
rounds and keep a stub only if DRC finds no violation on its new items:
  plane nets (/GND, /CELL16): a short track from each loose item to a via into the In1 plane
  other nets: a direct track on a shared outer layer, then via + B.Cu / In2.Cu track + via
Edits the board file as text (KiCad must be closed). Re-run is safe: it only adds items.

  python fix_unconnected.py [--rounds N]
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REVA = Path(__file__).resolve().parents[1]
PCB = REVA / "qfbms-rev-a.kicad_pcb"
CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
PLANE = {"/GND", "/CELL16"}
WIDTH = {"/GND": 0.4, "/CELL16": 0.4, "/3V3": 0.4, "/5V": 0.4, "/5V_BUCK": 0.4, "/VBUS": 0.4,
         "/PACK_F": 0.8, "/BAT_POS": 0.8, "/CHG_POS": 0.8, "/CHG_SRC": 0.8, "/CHG_NEG": 0.8}
COSMETIC = {"silk_over_copper", "silk_overlap", "silk_edge_clearance", "text_height",
            "lib_footprint_mismatch", "unconnected_items", "starved_thermal", "isolated_copper",
            "footprint_symbol_field_mismatch"}
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)]


def drc():
    out = Path(tempfile.mkdtemp()) / "drc.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones",
                    "-o", str(out), str(PCB)], capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))


def segments(text):
    segs = {}
    for m in re.finditer(r'\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)'
                         r'\s+\(width [\d.]+\)\s+\(layer "([^"]+)"\)\s+\(net "([^"]*)"\)\s+\(uuid "([^"]+)"\)', text):
        x0, y0, x1, y1 = map(float, m.group(1, 2, 3, 4))
        segs[m.group(7)] = ((x0, y0), (x1, y1), m.group(5))
    return segs


def layer_of(desc):
    if "PTH pad" in desc or desc.startswith("Via"):
        return "*"
    m = re.search(r" on ((?:F|B|In\d)\.Cu)", desc)
    return m.group(1) if m else "*"


def net_of(desc):
    m = re.search(r"\[(/[^\]]+)\]", desc)
    return m.group(1) if m else None


def seg_text(a, b, layer, net, w):
    u = str(uuid.uuid4())
    return u, (f'\t(segment\n\t\t(start {a[0]:.4f} {a[1]:.4f})\n\t\t(end {b[0]:.4f} {b[1]:.4f})\n'
               f'\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')


def via_text(p, net):
    u = str(uuid.uuid4())
    return u, (f'\t(via\n\t\t(at {p[0]:.4f} {p[1]:.4f})\n\t\t(size 0.5)\n\t\t(drill 0.25)\n'
               f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')


def candidates(a, b, net):
    """Candidate stub sets for one pair; each is a list of (kind, args)."""
    (pa, la), (pb, lb) = a, b
    w = WIDTH.get(net, 0.2)
    out = []
    outer = [l for l in ("F.Cu", "B.Cu") if l in (la, lb) or la == "*" or lb == "*"]
    if la == lb and la in ("F.Cu", "B.Cu"):
        outer = [la]
    if (la == lb or "*" in (la, lb)) and math.dist(pa, pb) < 6:
        for l in outer or ["F.Cu"]:
            out.append([("seg", pa, pb, l, w)])
    if net in PLANE:
        ends = [(p, l) for p, l in ((pa, la), (pb, lb)) if l not in ("In1.Cu",)]
        for d in (0.9, 1.3, 1.8):
            for dx, dy in DIRS:
                stubs = []
                for p, l in ends:
                    v = (p[0] + dx * d, p[1] + dy * d)
                    lay = l if l in ("F.Cu", "B.Cu") else "F.Cu"
                    stubs += [("seg", p, v, lay, w), ("via", v)]
                out.append(stubs)
    else:
        for d in (0.8, 1.2):
            for dx, dy in DIRS:
                va = (pa[0] + dx * d, pa[1] + dy * d)
                vb = (pb[0] + dx * d, pb[1] + dy * d)
                for mid in ("B.Cu", "In2.Cu"):
                    la2 = la if la in ("F.Cu", "B.Cu") else "F.Cu"
                    lb2 = lb if lb in ("F.Cu", "B.Cu") else "F.Cu"
                    out.append([("seg", pa, va, la2, w), ("via", va), ("seg", va, vb, mid, w),
                                ("via", vb), ("seg", vb, pb, lb2, w)])
    return out


def main():
    rounds = int(sys.argv[sys.argv.index("--rounds") + 1]) if "--rounds" in sys.argv else 24
    d = drc()
    text = PCB.read_text(encoding="utf-8")
    segs = segments(text)
    pairs = []
    for v in d.get("unconnected_items", []):
        it = v["items"]
        if len(it) != 2:
            continue
        net = net_of(it[0]["description"])
        pts = []
        for i, other in ((it[0], it[1]), (it[1], it[0])):
            p = (i["pos"]["x"], i["pos"]["y"])
            if i["uuid"] in segs:
                s0, s1, lay = segs[i["uuid"]]
                op = (other["pos"]["x"], other["pos"]["y"])
                p = min((s0, s1), key=lambda q: math.dist(q, op))
            pts.append((p, layer_of(i["description"])))
        pairs.append({"net": net, "a": pts[0], "b": pts[1], "cands": candidates(pts[0], pts[1], net),
                      "ids": {it[0]["uuid"], it[1]["uuid"]}, "done": False, "k": 0})
    print(f"{len(pairs)} unconnected pairs")
    for r in range(rounds):
        todo = [p for p in pairs if not p["done"] and p["k"] < len(p["cands"])]
        if not todo:
            break
        text = PCB.read_text(encoding="utf-8")
        added = {}
        chunks = []
        for i, p in enumerate(todo):
            ids = []
            for item in p["cands"][p["k"]]:
                if item[0] == "seg":
                    _, a, b, lay, w = item
                    if math.dist(a, b) < 0.01:
                        continue
                    u, t = seg_text(a, b, lay, p["net"], w)
                else:
                    u, t = via_text(item[1], p["net"])
                ids.append(u)
                chunks.append(t)
            added[i] = ids
        cut = text.rstrip().rfind(")")
        PCB.write_text(text[:cut] + "".join(chunks) + text[cut:], encoding="utf-8")
        d = drc()
        bad = set()
        for v in d.get("violations", []):
            if v["type"] in COSMETIC:
                continue
            for it in v.get("items", []):
                bad.add(it["uuid"])
        still = set()
        for v in d.get("unconnected_items", []):
            for it in v["items"]:
                still.add(it["uuid"])
        remove = []
        for i, p in enumerate(todo):
            ids = added[i]
            if any(u in bad for u in ids):
                remove += ids
                p["k"] += 1
            elif p["ids"] & still:
                remove += ids   # legal but did not connect: try the next one
                p["k"] += 1
            else:
                p["done"] = True
        if remove:
            text = PCB.read_text(encoding="utf-8")
            for u in remove:
                text = re.sub(r'\t\((?:segment|via)\n(?:\t\t[^\n]*\n)*?\t\t\(uuid "' + u + r'"\)\n\t\)\n', "", text)
            PCB.write_text(text, encoding="utf-8")
        print(f"round {r + 1}: {sum(p['done'] for p in pairs)}/{len(pairs)} closed")
    left = [p for p in pairs if not p["done"]]
    for p in left:
        print("  open:", p["net"], p["a"], p["b"])
    return len(left)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
