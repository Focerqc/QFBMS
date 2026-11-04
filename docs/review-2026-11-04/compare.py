"""Compare KiCad XML electrically. Run from any directory with Python 3."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Circuit:
    def __init__(self, filename):
        root = ET.parse(HERE / filename)
        self.parts = {c.get("ref"): c.findtext("value") for c in root.findall(".//components/comp")}
        self.pins = {(c.get("ref"), p.get("num")) for c in root.findall(".//components/comp")
                     for p in c.findall("units/unit/pins/pin")}
        self.nets = {}
        self.by_pin = {}
        self.nc = set()
        for net in root.findall(".//nets/net"):
            group = frozenset((n.get("ref"), n.get("pin")) for n in net)
            assert group and group not in self.nets
            self.nets[group] = net.get("name")
            for p in group:
                assert p not in self.by_pin
                self.by_pin[p] = group
            self.nc.update((n.get("ref"), n.get("pin")) for n in net if "no_connect" in n.get("pintype", ""))


def pins(group):
    return " ".join(".".join(p) for p in sorted(group))


def emit(filename, lines):
    (HERE / filename).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


before, after, main = (Circuit(n + ".xml") for n in ("baseline", "monitor", "main"))
lines = ["# Full hierarchy pin comparison", "",
         "Compare electrically equivalent groups by membership, ignoring labels and net codes.",
         f"Parts {len(before.parts)} → {len(after.parts)}. Added {sorted(after.parts.keys()-before.parts.keys())}, removed {sorted(before.parts.keys()-after.parts.keys())}.",
         f"Declared pins {len(before.pins)} → {len(after.pins)}. Added [{pins(after.pins-before.pins)}], removed [{pins(before.pins-after.pins)}].",
         f"Unchanged groups {len(before.nets.keys() & after.nets.keys())}.",
         "Each removed host bus group splits into two. This removes the direct powered-off path. No joined groups.", ""]
for title, circuit, other in [("Before", before, after), ("After", after, before)]:
    lines.append("## " + title)
    for g in sorted(circuit.nets.keys()-other.nets.keys(), key=pins):
        lines.append(f"- {circuit.nets[g]} — {pins(g)}")
    lines.append("Declared pins absent from nets — " + (pins(circuit.pins-circuit.by_pin.keys()) or "none"))
    lines.append("All NC-typed pins — " + pins(circuit.nc))
    lines.append("Singletons (every member and classification)")
    for g, name in circuit.nets.items():
        if len(g) == 1:
            why = "intentional NC / unresolved port" if g <= circuit.nc else "external cell tap; harness absent" if name.startswith("CELL") else "unexpected floating pin"
            lines.append(f"- {pins(g)} — {name} — {why}")
emit("netlist-comparison.md", lines)

lines = ["# Main schematic reconciliation", "", "Read-only XML from the main schematic. Pin numbers refer to symbols, not inferred PCB pads.",
         "Both BQs match by reference and role. Each line gives monitor and main peer sets including the pin itself. Different filter reference names require mapping through the actual cell index before migration.",
         "Main Q1 is a power-switch reference collision, not the monitor preregulator. U205 is a logical host port, not a package.",
         "Monitor references absent by name in main: " + ", ".join(sorted(after.parts.keys()-main.parts.keys())),
         "Map R_F and C_F cell-by-cell. Add admission, isolation, local supplies, decoupling, TS2 ports and independent upper current ties only after review. Keep physical harness/bleed placement fixed.",
         "Main joins both BQ grounds, SDA, SCL, SRP and SRN across domains. Separate those nets and supply returns. Preserve genuine NC pin intent. Reconcile the main BQ exposed pads against the footprint separately.", ""]
for ref in ("U_BQ1", "U_BQ2"):
    lines.append("## " + ref)
    for p in sorted((p for p in (after.pins | main.pins) if p[0]==ref), key=lambda p:int(p[1])):
        a,m=after.by_pin.get(p,frozenset()),main.by_pin.get(p,frozenset())
        status = "same member set" if a and a==m else "review differing peers" if a and m else "pin absent from one export"
        lines.append(f"- {pins([p])} ({status}) — draft {after.nets.get(a,'absent')} [{pins(a)}]; main {main.nets.get(m,'absent')} [{pins(m)}]")
emit("main-reconciliation.md", lines)

def findings(filename):
    report=json.loads((HERE / filename).read_text())
    return sorted((s["path"], v["type"], v["severity"], sorted(i["description"] for i in v["items"]))
                  for s in report["sheets"] for v in s["violations"])

assert findings("erc.json")==findings("baseline-erc.json")
assert before.pins==after.pins and before.parts==after.parts
assert len(before.nets.keys()-after.nets.keys())==2 and len(after.nets.keys()-before.nets.keys())==4
for bus, host_pin, switch_pin, bq_pin, resistor in [("SDA","1","4","27","R20"),("SCL","2","6","26","R21")]:
    assert after.by_pin["U205",host_pin]=={("U205",host_pin),("U204",switch_pin)}
    assert after.by_pin["U_BQ1",bq_pin]=={("U_BQ1",bq_pin),(resistor,"1")}
upper_ground=after.by_pin["U_BQ2","17"]
assert after.nets[upper_ground]=="CELL16" and all(("U_BQ2",p) in upper_ground for p in ("18","20","49"))
