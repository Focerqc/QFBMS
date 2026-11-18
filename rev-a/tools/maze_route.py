"""Close the connections DRC still reports as unconnected with a small grid router.

A* on a 0.1 mm grid over F.Cu, In2.Cu and B.Cu (In1 holds the planes), vias between them.
Obstacles are every other net's pads, tracks and vias, inflated by the clearance the pair
needs (0.6 mm if either net is a pack-level CHARGE/HV net, else 0.15 mm) plus half the track
width. Pours of other nets are passable: they refill around the new copper. Each routed
connection becomes an obstacle for the next. Tracks and vias are appended to the board file.

Run with KiCad's python.exe (numpy + pcbnew), board closed in KiCad:
  python.exe maze_route.py
"""
import heapq
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import numpy as np
import pcbnew

REVA = Path(__file__).resolve().parents[1]
PCB = REVA / "qfbms-rev-a.kicad_pcb"
CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
RES = 0.1
LAYERS = ["F.Cu", "In2.Cu", "B.Cu"]
HV = {"/PACK_F", "/BAT_POS", "/CHG_POS", "/CHG_SRC", "/CHG_NEG", "/VIN_BUCK", "/SW", "/CHG_GATE"}
WIDTH = {"/GND": 0.3, "/CELL16": 0.3}
VIA_R = 0.25
VIA_COST = 20.0


LOW_DV = [{"/CHG_GATE", "/CHG_SRC"}, {"/SW", "/ANODE"}, {"/VIN_BUCK", "/PACK_F"}]


def clr(a, b):
    if any({a, b} <= s for s in LOW_DV):
        return 0.18
    return (0.6 if (a in HV or b in HV) else 0.15) + 0.03


WOVR = {}


def width(net):
    if net in WOVR:
        return WOVR[net]
    return WIDTH.get(net, 0.4 if net in HV else 0.2)


def drc():
    out = Path(tempfile.mkdtemp()) / "drc.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--refill-zones", "-o", str(out), str(PCB)],
                   capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))


class Board:
    def __init__(self):
        text = PCB.read_text(encoding="utf-8")
        self.segs = []   # (x0, y0, x1, y1, w, layer, net, uuid)
        for m in re.finditer(r'\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)'
                             r'\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net "([^"]*)"\)\s+\(uuid "([^"]+)"\)',
                             text):
            x0, y0, x1, y1, w = map(float, m.group(1, 2, 3, 4, 5))
            self.segs.append((x0, y0, x1, y1, w, m.group(6), m.group(7), m.group(8)))
        self.vias = []   # (x, y, r, net, uuid)
        for m in re.finditer(r'\(via\s+\(at ([-\d.]+) ([-\d.]+)\)\s+\(size ([\d.]+)\)\s+\(drill [\d.]+\)'
                             r'\s+\(layers [^)]*\)\s+\(net "([^"]*)"\)\s+\(uuid "([^"]+)"\)', text):
            self.vias.append((float(m.group(1)), float(m.group(2)), float(m.group(3)) / 2, m.group(4), m.group(5)))
        self.fills = []  # (net, layer, np.array pts)
        for z in re.finditer(r'\n\t\(zone\n', text):
            end = text.find("\n\t)\n", z.start() + 1)
            blk = text[z.start():end]
            net = re.search(r'\(net "([^"]*)"\)', blk)
            net = net.group(1) if net else ""
            for fp in re.finditer(r'\(filled_polygon\s+\(layer "([^"]+)"\)\s+\(pts(.*?)\n\t\t\t\)\n\t\t\)', blk, re.S):
                pts = np.array([[float(a), float(b)] for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', fp.group(2))])
                if len(pts) > 2:
                    self.fills.append((net, fp.group(1), pts))
        b = pcbnew.LoadBoard(str(PCB))
        self.pads = []   # (x0, y0, x1, y1, layers set, net, ref, num)
        for fp in list(b.GetFootprints()):
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                lays = {l for l in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
                        if p.IsOnLayer(getattr(pcbnew, l.replace(".", "_")))}
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    lays = {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"}
                self.pads.append((pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()),
                                  pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()),
                                  lays, p.GetNetname(), fp.GetReference(), p.GetNumber()))
        eb = b.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = pcbnew.ToMM(eb.GetX()), pcbnew.ToMM(eb.GetY())
        self.x1, self.y1 = pcbnew.ToMM(eb.GetRight()), pcbnew.ToMM(eb.GetBottom())
        self.nx = int((self.x1 - self.x0) / RES) + 1
        self.ny = int((self.y1 - self.y0) / RES) + 1
        self.new = []    # text chunks

    # grid helpers
    def cell(self, x, y):
        return int(round((y - self.y0) / RES)), int(round((x - self.x0) / RES))

    def xy(self, r, c):
        return self.x0 + c * RES, self.y0 + r * RES

    def grids(self, net):
        """Blocked cells per layer for tracks of `net`, and for vias of `net`."""
        w = width(net)
        tr = {l: np.zeros((self.ny, self.nx), bool) for l in LAYERS}
        via = np.zeros((self.ny, self.nx), bool)
        yy, xx = np.mgrid[0:self.ny, 0:self.nx]
        X = self.x0 + xx * RES
        Y = self.y0 + yy * RES

        def mark_rect(g, x0, y0, x1, y1, r):
            r0, c0 = self.cell(x0 - r, y0 - r)
            r1, c1 = self.cell(x1 + r, y1 + r)
            g[max(r0, 0):max(r1 + 1, 0), max(c0, 0):max(c1 + 1, 0)] = True

        def mark_seg(g, x0, y0, x1, y1, r):
            r0, c0 = self.cell(min(x0, x1) - r, min(y0, y1) - r)
            r1, c1 = self.cell(max(x0, x1) + r, max(y0, y1) + r)
            r0, c0 = max(r0, 0), max(c0, 0)
            sx, sy = X[r0:r1 + 1, c0:c1 + 1], Y[r0:r1 + 1, c0:c1 + 1]
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy
            t = np.clip(((sx - x0) * dx + (sy - y0) * dy) / L2, 0, 1) if L2 > 0 else 0
            d = np.hypot(sx - (x0 + t * dx), sy - (y0 + t * dy))
            g[r0:r1 + 1, c0:c1 + 1] |= d <= r

        for (x0, y0, x1, y1, lays, pnet, _, _) in self.pads:
            if pnet == net and pnet:
                continue
            c = clr(net, pnet)
            for l in LAYERS:
                if l in lays:
                    mark_rect(tr[l], x0, y0, x1, y1, c + w / 2)
            if lays & {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"}:
                mark_rect(via, x0, y0, x1, y1, c + VIA_R)
        for (x0, y0, x1, y1, sw, l, snet, _) in self.segs:
            if snet == net:
                continue
            c = clr(net, snet)
            if l in tr:
                mark_seg(tr[l], x0, y0, x1, y1, c + w / 2 + sw / 2)
            mark_seg(via, x0, y0, x1, y1, c + VIA_R + sw / 2)
        for (x, y, r, vnet, _) in self.vias:
            if vnet == net:
                continue
            c = clr(net, vnet)
            for l in LAYERS:
                mark_seg(tr[l], x, y, x, y, c + w / 2 + r)
            mark_seg(via, x, y, x, y, c + VIA_R + r)
        edge = 0.75
        for g in list(tr.values()) + [via]:
            m = int((edge + 0.25) / RES)
            g[:m, :] = g[-m:, :] = True
            g[:, :m] = g[:, -m:] = True
        return tr, via

    def item_cells(self, desc, pos, net):
        """Cells (layer index, row, col) belonging to one DRC item."""
        out = set()
        m = re.match(r"(?:PTH )?[Pp]ad (\S+) \[[^\]]*\] of (\S+)", desc)
        if m:
            num, ref = m.group(1), m.group(2)
            for (x0, y0, x1, y1, lays, pnet, r, n) in self.pads:
                if r == ref and n == num:
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    hx, hy = max((x1 - x0) / 2 - 0.1, 0.05), max((y1 - y0) / 2 - 0.1, 0.05)
                    r0, c0 = self.cell(cx - hx, cy - hy)
                    r1, c1 = self.cell(cx + hx, cy + hy)
                    for li, l in enumerate(LAYERS):
                        if l in lays:
                            out |= {(li, rr, cc) for rr in range(r0, r1 + 1) for cc in range(c0, c1 + 1)}
            return out
        if desc.startswith("Track"):
            px, py = pos["x"], pos["y"]
            best = min(self.segs, key=lambda s: min(math.dist((s[0], s[1]), (px, py)),
                                                    math.dist((s[2], s[3]), (px, py)),
                                                    math.dist(((s[0] + s[2]) / 2, (s[1] + s[3]) / 2), (px, py)))
                       if s[6] == net else 1e9)
            x0, y0, x1, y1, _, l, _, _ = best
            n = max(int(math.dist((x0, y0), (x1, y1)) / RES), 1)
            for i in range(n + 1):
                x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                for li, ll in enumerate(LAYERS):
                    if l == "In1.Cu":
                        out.add((li, *self.cell(x, y), "via"))
                    elif ll == l:
                        out.add((li, *self.cell(x, y)))
            return out
        if desc.startswith("Via"):
            px, py = pos["x"], pos["y"]
            v = min(self.vias, key=lambda v: math.dist((v[0], v[1]), (px, py)) if v[3] == net else 1e9)
            for li in range(len(LAYERS)):
                out.add((li, *self.cell(v[0], v[1])))
            return out
        if desc.startswith("Zone"):
            lm = re.search(r" on ((?:F|B|In\d)\.Cu)", desc)
            l = lm.group(1)
            px, py = pos["x"], pos["y"]
            polys = [p for (n, ll, p) in self.fills if n == net and ll == l]
            if not polys:
                return out
            poly = min(polys, key=lambda p: np.min(np.hypot(p[:, 0] - px, p[:, 1] - py)))
            if l not in LAYERS:   # In1 plane piece: reachable through a via anywhere inside
                l, via_only = "In1", True
            r0, c0 = self.cell(poly[:, 0].min(), poly[:, 1].min())
            r1, c1 = self.cell(poly[:, 0].max(), poly[:, 1].max())
            rr, cc = np.mgrid[r0:r1 + 1, c0:c1 + 1]
            X, Y = self.x0 + cc * RES, self.y0 + rr * RES
            inside = np.zeros(X.shape, bool)
            xs, ys = poly[:, 0], poly[:, 1]
            j = len(xs) - 1
            for i in range(len(xs)):
                cond = ((ys[i] > Y) != (ys[j] > Y)) & (X < (xs[j] - xs[i]) * (Y - ys[i]) / (ys[j] - ys[i] + 1e-12) + xs[i])
                inside ^= cond
                j = i
            idx = np.argwhere(inside)[::4]
            for a, b in idx:
                if l == "In1":
                    out |= {(li, r0 + a, c0 + b, "via") for li in range(len(LAYERS))}
                else:
                    out.add((LAYERS.index(l), r0 + a, c0 + b))
            return out
        return out

    def route(self, net, src, dst):
        tr, via = self.grids(net)
        blocked = np.stack([tr[l] for l in LAYERS])
        need_via_dst = {(c[0], c[1], c[2]) for c in dst if len(c) == 4}
        need_via_src = {(c[0], c[1], c[2]) for c in src if len(c) == 4}
        src = {(c[0], c[1], c[2]) for c in src}
        dst = {(c[0], c[1], c[2]) for c in dst}
        # the items' own cells are free even if inflated neighbours overlap them
        for (l, r, c) in src | dst:
            if 0 <= r < self.ny and 0 <= c < self.nx:
                blocked[l, r, c] = False
        tr_d = np.array(sorted({(c[1], c[2]) for c in dst}))
        if len(tr_d) > 300:
            tr_d = tr_d[np.linspace(0, len(tr_d) - 1, 300).astype(int)]
        def h(r, c):
            return float(np.min(np.abs(tr_d[:, 0] - r) + np.abs(tr_d[:, 1] - c))) * 0.8
        pq, came, cost = [], {}, {}
        for s in src:
            if s in need_via_src and via[s[1], s[2]]:
                continue
            cost[s] = 0.0
            heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
        moves = [(0, 1, 1), (0, -1, 1), (1, 0, 1), (-1, 0, 1), (1, 1, 1.42), (1, -1, 1.42), (-1, 1, 1.42), (-1, -1, 1.42)]
        n = 0
        while pq:
            _, g, cur = heapq.heappop(pq)
            if g > cost.get(cur, 1e18):
                continue
            n += 1
            if n > 2_500_000:
                return None
            if cur in dst and (cur not in need_via_dst or not via[cur[1], cur[2]]):
                path = [cur]
                while path[-1] in came:
                    path.append(came[path[-1]])
                return path[::-1], cur in need_via_dst, path[-1] in need_via_src
            l, r, c = cur
            nbrs = []
            for dr, dc, k in moves:
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.ny and 0 <= cc < self.nx and not blocked[l, rr, cc]:
                    if dr and dc and (blocked[l, r, cc] or blocked[l, rr, c]):
                        continue
                    nbrs.append(((l, rr, cc), k))
            if not via[r, c]:
                for l2 in range(len(LAYERS)):
                    if l2 != l and not blocked[l2, r, c]:
                        nbrs.append(((l2, r, c), VIA_COST))
            for nxt, k in nbrs:
                ng = g + k
                if ng < cost.get(nxt, 1e18):
                    cost[nxt] = ng
                    came[nxt] = cur
                    heapq.heappush(pq, (ng + h(nxt[1], nxt[2]), ng, nxt))
        return None

    def emit(self, net, path, via_end, via_start):
        w = width(net)
        pts = [(l, *self.xy(r, c)) for (l, r, c) in path]
        def via(x, y):
            u = str(uuid.uuid4())
            self.new.append(f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size 0.5)\n\t\t(drill 0.25)\n'
                            f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')
            self.vias.append((x, y, VIA_R, net, u))
        def seg(a, b, l):
            u = str(uuid.uuid4())
            self.new.append(f'\t(segment\n\t\t(start {a[0]:.4f} {a[1]:.4f})\n\t\t(end {b[0]:.4f} {b[1]:.4f})\n'
                            f'\t\t(width {w})\n\t\t(layer "{LAYERS[l]}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')
            self.segs.append((a[0], a[1], b[0], b[1], w, LAYERS[l], net, u))
        if via_start:
            via(pts[0][1], pts[0][2])
        start = 0
        for i in range(1, len(pts)):
            if pts[i][0] != pts[i - 1][0]:
                if i - 1 > start:
                    seg(pts[start][1:], pts[i - 1][1:], pts[start][0])
                via(pts[i][1], pts[i][2])
                start = i
                continue
            if i + 1 < len(pts) and pts[i + 1][0] == pts[i][0]:
                d1 = (round((pts[i][1] - pts[i - 1][1]) / RES), round((pts[i][2] - pts[i - 1][2]) / RES))
                d2 = (round((pts[i + 1][1] - pts[i][1]) / RES), round((pts[i + 1][2] - pts[i][2]) / RES))
                if d1 == d2:
                    continue
            if i > start:
                seg(pts[start][1:], pts[i][1:], pts[i][0])
                start = i
        if via_end:
            via(pts[-1][1], pts[-1][2])


def main():
    d = drc()
    dang = [it["uuid"] for v in d.get("violations", []) if v["type"] in ("track_dangling", "via_dangling")
            for it in v["items"]]
    dang += [it["uuid"] for v in d.get("violations", []) if v["type"] == "copper_edge_clearance"
             for it in v["items"] if it["description"].startswith(("Track", "Via"))]
    if dang:
        text = PCB.read_text(encoding="utf-8")
        for u in dang:
            text = re.sub(r'\t\((?:segment|via)\n(?:\t\t[^\n]*\n)*?\t\t\(uuid "' + u + r'"\)\n\t\)\n', "", text)
        PCB.write_text(text, encoding="utf-8")
        print(f"removed {len(dang)} dangling items")
        d = drc()
    pairs = [v["items"] for v in d.get("unconnected_items", []) if len(v["items"]) == 2]
    print(f"{len(pairs)} unconnected pairs")
    bd = Board()
    ok, fail = 0, []
    for a, b in pairs:
        net = re.search(r"\[(/[^\]]+)\]", a["description"]).group(1)
        src = bd.item_cells(a["description"], a["pos"], net)
        dst = bd.item_cells(b["description"], b["pos"], net)
        if net in ("/GND", "/CELL16"):   # any via into this net's In1 plane also connects
            for (n, l, poly) in bd.fills:
                if n == net and l == "In1.Cu":
                    cx, cy = poly[:, 0].mean(), poly[:, 1].mean()
                    dst |= bd.item_cells(f"Zone [{net}] on In1.Cu", {"x": cx, "y": cy}, net)
        if not src or not dst:
            fail.append((net, a["description"], b["description"], "no cells"))
            continue
        res = None
        for w in (None, 0.2, 0.15):
            if w:
                WOVR[net] = w
            res = bd.route(net, src, dst)
            WOVR.pop(net, None)
            if res and len(res[0]) > 1:
                break
            res = None
        if not res:
            fail.append((net, a["description"], b["description"], "no path"))
            continue
        path, via_end, via_start = res
        if w:
            WOVR[net] = w
        bd.emit(net, path, via_end, via_start)
        WOVR.pop(net, None)
        ok += 1
        print(f"  routed {net}: {a['description'][:40]} -> {b['description'][:40]} ({len(path)} cells)")
    text = PCB.read_text(encoding="utf-8")
    cut = text.rstrip().rfind(")")
    PCB.write_text(text[:cut] + "".join(bd.new) + text[cut:], encoding="utf-8")
    print(f"routed {ok}, failed {len(fail)}")
    for f in fail:
        print("  FAIL", f)


if __name__ == "__main__":
    main()
