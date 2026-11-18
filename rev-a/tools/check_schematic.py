"""Check the generated schematic with kicad-cli: netlist parity with circuit.py, and ERC.

kicad-cli is ground truth. Exit code 1 on any netlist mismatch or ERC error.
"""
import collections
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import circuit

REVA = Path(__file__).resolve().parents[1]
SCH = REVA / "qfbms-rev-a.kicad_sch"
CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")


def netlist(out):
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(SCH)],
                   check=True, capture_output=True)
    root = ET.parse(out).getroot()
    pin_net = {}
    members = collections.defaultdict(list)
    for n in root.iter("net"):
        name = n.get("name").lstrip("/")
        for nd in n.iter("node"):
            pin_net[(nd.get("ref"), nd.get("pin"))] = name
            members[name].append((nd.get("ref"), nd.get("pin")))
    comps = {c.get("ref"): c for c in root.iter("comp")}
    return pin_net, members, comps


def main():
    tmp = Path(tempfile.mkdtemp())
    pin_net, members, comps = netlist(tmp / "rev-a.xml")
    problems = []
    want_refs = {p["ref"] for p in circuit.PARTS}
    got_refs = set(comps)
    for r in sorted(want_refs - got_refs):
        problems.append(f"missing in schematic: {r}")
    for r in sorted(got_refs - want_refs):
        problems.append(f"extra in schematic: {r}")
    for p in circuit.PARTS:
        for pin, net in p["pins"].items():
            got = pin_net.get((p["ref"], pin))
            if got != net:
                problems.append(f"{p['ref']}.{pin}: table {net}, schematic {got}")
    singles = sorted(n for n, m in members.items()
                     if len(m) == 1 and not n.startswith("unconnected-"))
    for n in singles:
        problems.append(f"single-pin net {n}: {members[n]}")
    erc = tmp / "erc.json"
    subprocess.run([CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", str(erc), str(SCH)],
                   capture_output=True)
    data = json.loads(erc.read_text(encoding="utf-8"))
    counts = collections.Counter()
    shown = []
    for sheet in data.get("sheets", []):
        for v in sheet.get("violations", []):
            counts[(v["severity"], v["type"])] += 1
            if v["severity"] == "error" or len(shown) < 40:
                items = "; ".join(i.get("description", "") for i in v.get("items", []))
                shown.append(f"  [{v['severity']}] {v['type']}: {v['description']} | {items}")
    print(f"components {len(got_refs)}, nets {len(members)}, table pins checked "
          f"{sum(len(p['pins']) for p in circuit.PARTS)}")
    print("ERC:", dict(counts) or "clean")
    for s in shown:
        print(s)
    for pr in problems:
        print("NETLIST:", pr)
    errors = sum(c for (sev, _), c in counts.items() if sev == "error")
    sys.exit(1 if problems or errors else 0)


if __name__ == "__main__":
    main()
