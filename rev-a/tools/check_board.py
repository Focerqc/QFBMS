"""DRC + schematic parity for the rev A board, sorted into real problems and known items.

Known, not layout problems:
  - pinout: two pads of the same part (e.g. BQ76952 PACK next to LD). Set by the chip maker.
  - fixed: violations that involve only the fixed parts' own footprints (connectors, USB-C, XT30).
Writes rev-a/route/drc-summary.json. Exit 1 if anything real is left.
"""
import collections
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import circuit  # noqa: E402

REVA = Path(__file__).resolve().parents[1]
PCB = REVA / "qfbms-rev-a.kicad_pcb"
CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
FIXED = {p["ref"] for p in circuit.PARTS if p["fixed"]}
IGNORE = {"silk_over_copper", "silk_overlap", "silk_edge_clearance", "text_height", "lib_footprint_mismatch"}


def owner(desc):
    m = re.search(r" of (\S+) on ", desc) or re.search(r"Footprint (\S+)", desc)
    return m.group(1) if m else None


def main():
    out = Path(tempfile.mkdtemp()) / "drc.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity", "--refill-zones",
                    "-o", str(out), str(PCB)], capture_output=True)
    d = json.loads(out.read_text(encoding="utf-8"))
    real, pinout, fixed, ignored = [], [], [], collections.Counter()
    for v in d.get("violations", []):
        if v["type"] in IGNORE:
            ignored[v["type"]] += 1
            continue
        descs = [i["description"] for i in v.get("items", [])]
        owners = [owner(x) for x in descs]
        rec = f"{v['type']}: " + " ; ".join(descs)
        if len(owners) == 2 and owners[0] and owners[0] == owners[1] and all(x.startswith("Pad") for x in descs):
            pinout.append(rec)
        elif owners and all(o in FIXED for o in owners if o) and any(owners) and \
                all(("Edge.Cuts" in x) or owner(x) in FIXED or "NPTH" in x for x in descs):
            fixed.append(rec)
        else:
            real.append(rec)
    unconnected = [" ; ".join(i["description"] for i in v["items"]) for v in d.get("unconnected_items", [])]
    parity = [f"{v['type']}: {v['description']}" for v in d.get("schematic_parity", [])]
    summary = {"real": len(real), "unconnected": len(unconnected), "parity": len(parity),
               "pinout_pairs": len(pinout), "fixed_footprint": len(fixed), "ignored_cosmetic": dict(ignored)}
    (REVA / "route").mkdir(exist_ok=True)
    (REVA / "route" / "drc-summary.json").write_text(json.dumps(
        {"summary": summary, "real": real, "unconnected": unconnected, "parity": parity,
         "pinout": pinout, "fixed": fixed}, indent=1), encoding="utf-8")
    print(json.dumps(summary))
    by = collections.Counter(r.split(":")[0] for r in real)
    print("real by type:", dict(by))
    for r in real[:25]:
        print("  ", r[:200])
    for u in unconnected[:15]:
        print("  U", u[:180])
    for p in parity[:10]:
        print("  P", p[:180])
    sys.exit(1 if real or unconnected or parity else 0)


if __name__ == "__main__":
    main()
