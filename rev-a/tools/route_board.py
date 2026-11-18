"""Route rev A with Freerouting via Specctra DSN/SES, then add copper zones.

  python.exe route_board.py export   -> rev-a/route/qfbms-rev-a.dsn
  (run Freerouting on it; see README)  -> rev-a/route/qfbms-rev-a.ses
  python.exe route_board.py import   -> tracks into qfbms-rev-a.kicad_pcb, then zones

Zones: In1.Cu is a GND plane over the GND-domain areas and a CELL16 plane over the upper
domain, with a 1.2 mm gap between them. The charge path gets pours on F.Cu/B.Cu.
Run with KiCad 10's python.exe. The board file must be closed in KiCad.
"""
import sys
from pathlib import Path

import pcbnew

REVA = Path(__file__).resolve().parents[1]
PCB = REVA / "qfbms-rev-a.kicad_pcb"
OUT = REVA / "route"
DSN = OUT / "qfbms-rev-a.dsn"
SES = OUT / "qfbms-rev-a.ses"
MM = pcbnew.FromMM


def zone(board, net, layer, pts, priority=0, clearance=0.15, min_width=0.2):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(min_width))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.4))
    outline = z.Outline()
    outline.NewOutline()
    for x, y in pts:
        outline.Append(MM(x), MM(y))
    board.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def add_planes(board):
    """In1.Cu reference planes: CELL16 under the upper domain, GND elsewhere, 1.2 mm apart."""
    zone(board, "/CELL16", pcbnew.In1_Cu, [(40.6, 0.3), (63.0, 0.3), (63.0, 20.6), (69.4, 20.6),
                                           (69.4, 31.8), (35.0, 31.8), (35.0, 20.6), (40.6, 20.6)])
    zone(board, "/GND", pcbnew.In1_Cu, [(0.3, 0.3), (39.4, 0.3), (39.4, 19.4), (33.8, 19.4),
                                        (33.8, 31.8), (0.3, 31.8)])
    zone(board, "/GND", pcbnew.In1_Cu, [(64.2, 0.3), (129.8, 0.3), (129.8, 31.8), (70.6, 31.8),
                                        (70.6, 19.4), (64.2, 19.4)])


def add_pours(board):
    """Charge path: one shaped pour per net (pad positions from the placed board), and
    outer-layer GND/CELL16 fill elsewhere. Charge-current return GND runs on the In1 plane."""
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    zone(board, "/CHG_POS", F, rect(12.8, 0.4, 21.3, 12.4), priority=2, clearance=0.6)
    zone(board, "/CHG_SRC", F, rect(25.6, 0.4, 30.6, 25.2), priority=2, clearance=0.6)
    zone(board, "/PACK_F", F, [(15.4, 13.4), (25.3, 13.4), (25.3, 31.6), (18.6, 31.6), (18.6, 25.2),
                               (15.4, 25.2)], priority=2, clearance=0.6)
    zone(board, "/BAT_POS", F, [(11.6, 25.4), (18.3, 25.4), (18.3, 31.6), (11.6, 31.6)], priority=2,
         clearance=0.6)
    zone(board, "/CHG_NEG", B, rect(13.0, 0.4, 33.6, 31.6), priority=2, clearance=0.6)
    zone(board, "/CHG_NEG", F, rect(31.0, 25.6, 33.6, 31.6), priority=2, clearance=0.6)
    for layer in (F, B):
        zone(board, "/GND", layer, rect(33.8, 0.3, 39.4, 31.8), priority=0)
        zone(board, "/GND", layer, [(64.2, 0.3), (129.8, 0.3), (129.8, 31.8), (70.6, 31.8),
                                    (70.6, 19.4), (64.2, 19.4)], priority=0)
        zone(board, "/CELL16", layer, rect(40.6, 0.3, 63.0, 19.4), priority=0)


def fill(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def main():
    OUT.mkdir(exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "export"
    board = pcbnew.LoadBoard(str(PCB))
    if mode == "export":
        if board.GetAreaCount() == 0:
            add_planes(board)
        fill(board)
        pcbnew.SaveBoard(str(PCB), board)
        ok = pcbnew.ExportSpecctraDSN(board, str(DSN))
        print("DSN", ok, DSN)
    elif mode == "import":
        ok = pcbnew.ImportSpecctraSES(board, str(SES))
        print("SES import", ok)
        if not ok:
            raise SystemExit(1)
        if "--no-pours" not in sys.argv:
            add_pours(board)
        fill(board)
        pcbnew.SaveBoard(str(PCB), board)
        print("saved", PCB)


if __name__ == "__main__":
    main()
