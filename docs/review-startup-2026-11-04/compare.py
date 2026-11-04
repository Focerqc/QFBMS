"""Compare full pin membership, ignoring KiCad net codes and generated names."""
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent


def snapshot(path):
    tree = ET.parse(path)
    declared = {f"{c.get('ref')}.{p.get('num')}" for c in tree.findall(".//components/comp")
                for p in c.findall("units/unit/pins/pin")}
    groups = {}
    nc = set()
    attached = set()
    for net in tree.findall(".//nets/net"):
        pins = frozenset(f"{n.get('ref')}.{n.get('pin')}" for n in net)
        assert not attached.intersection(pins)
        attached.update(pins)
        groups[pins] = net.get("name")
        nc.update(f"{n.get('ref')}.{n.get('pin')}" for n in net if "no_connect" in n.get("pintype",""))
    assert attached <= declared
    return declared, groups, nc, declared - attached


def findings(path):
    report = json.loads(path.read_text())
    return Counter((s["path"], v["type"], v["severity"], tuple(sorted(i["description"] for i in v["items"])))
                   for s in report["sheets"] for v in s["violations"])


before = snapshot(HERE / "before.xml")
assert before == snapshot(HERE.parent / "review-2026-11-04/monitor.xml")
after = snapshot(HERE / "monitor.xml")
for title, a, b in [("Before",before,after),("After",after,before)]:
    pins, groups, nc, missing = a
    print(title, len(pins), "declared pins;",len(groups),"groups")
    print("Pins unique to this version:",sorted(pins-b[0]))
    print("Absent from nets:",sorted(missing))
    print("No-connect types:",sorted(nc))
    print("Singletons:",sorted((next(iter(g)),n) for g,n in groups.items() if len(g)==1))
    for g in sorted(groups.keys()-b[1].keys(), key=lambda g:sorted(g)):
        print(groups[g], " ".join(sorted(g)))
old = findings(HERE.parent / "review-2026-11-04/erc.json")
new = findings(HERE / "erc.json")
print("ERC removed",old-new,"added",new-old)
