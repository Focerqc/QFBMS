"""Read qfbms32 and report harness, BQ76952, and copper progress.

Runs under KiCad's Python (needs pcbnew). Prints a single JSON object
after the marker @@JSON@@.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

import pcbnew

# KiCad symbol Battery_Management:BQ7695202PFB
BQ_PINS = [
    (1, "VC15"), (2, "VC14"), (3, "VC13"), (4, "VC12"), (5, "VC11"), (6, "VC10"),
    (7, "VC9"), (8, "VC8"), (9, "VC7"), (10, "VC6"), (11, "VC5"), (12, "VC4"),
    (13, "VC3"), (14, "VC2"), (15, "VC1"), (16, "VC0"), (17, "VSS"), (18, "SRP"),
    (19, "NC"), (20, "SRN"), (21, "TS1"), (22, "TS2"), (23, "TS3"), (24, "REG18"),
    (25, "ALERT"), (26, "SCL"), (27, "SDA"), (28, "SPI_MOSI"), (29, "CFETOFF"),
    (30, "DFETOFF"), (31, "DCHG"), (32, "DDSG"), (33, "RST_SHUT"), (34, "REG2"),
    (35, "REG1"), (36, "REGIN"), (37, "BREG"), (38, "FUSE"), (39, "PDSG"),
    (40, "PCHG"), (41, "LD"), (42, "PACK"), (43, "DSG"), (44, "NC"), (45, "CHG"),
    (46, "CP1"), (47, "BAT"), (48, "VC16"),
]
BQ_FUNC = {n: name for n, name in BQ_PINS}
CELL_CONNS = ("J_CELL1", "J_CELL2", "J_CELL3", "J_CELL4")
REG_PINS = (24, 34, 35, 36, 37)
DRIVER_PINS = (39, 40, 43, 45)


def net_of(pad) -> str:
    return pad.GetNetname() or ""


def is_signal(pad) -> bool:
    num = pad.GetNumber() or ""
    return num not in ("", "MP") and not num.startswith("TAB")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: audit.py BOARD", file=sys.stderr)
        sys.exit(2)
    board = pcbnew.LoadBoard(sys.argv[1])
    board.BuildConnectivity()
    conn = board.GetConnectivity()

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    index = {}
    pads_by_net = defaultdict(list)
    total_pads = 0
    unnetted = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            total_pads += 1
            pos = pad.GetPosition()
            index[(pos.x, pos.y)] = (fp.GetReference(), pad.GetNumber() or "", net_of(pad))
            name = net_of(pad)
            if name:
                pads_by_net[name].append((fp.GetReference(), pad.GetNumber() or ""))
            elif is_signal(pad):
                unnetted += 1

    n_via = n_trk = 0
    for item in board.GetTracks():
        if type(item).__name__ in ("PCB_VIA", "VIA") or getattr(item, "GetClass", lambda: "")() == "PCB_VIA":
            n_via += 1
        else:
            n_trk += 1

    cluster_cache = {}

    def cluster(pad):
        pos = pad.GetPosition()
        key = (pos.x, pos.y)
        if key in cluster_cache:
            return cluster_cache[key]
        found = []
        seen = set()
        try:
            items = list(conn.GetConnectedItems(pad))
        except Exception:
            items = []
        for it in items:
            if type(it).__name__ != "PAD":
                continue
            ip = it.GetPosition()
            ident = index.get((ip.x, ip.y))
            if not ident or ident[0:2] in seen:
                continue
            seen.add(ident[0:2])
            found.append(ident)
        me = index.get(key)
        if me and me[0:2] not in seen:
            found.append(me)
        cluster_cache[key] = found
        return found

    def pad(ref, num):
        fp = fps.get(ref)
        if not fp:
            return None
        return fp.FindPadByNumber(str(num))

    def reaches(pad_obj, pred) -> list:
        if not pad_obj:
            return []
        return [p for p in cluster(pad_obj) if pred(p)]

    def fmt_refs(pairs) -> str:
        refs = []
        for ref, num, _net in pairs:
            label = f"{ref}.{num}" if num else ref
            if label not in refs:
                refs.append(label)
        return ", ".join(refs[:8]) + ("…" if len(refs) > 8 else "")

    rows = []

    def add(group, label, expect, state, found, note=""):
        rows.append({
            "group": group,
            "label": label,
            "expect": expect,
            "state": state,
            "found": found,
            "note": note,
        })

    # --- harness names ---
    bat1 = pad("J_BAT1", "1")
    bat2 = pad("J_BAT1", "2")
    top = net_of(bat1) if bat1 else ""
    bot = net_of(bat2) if bat2 else ""
    top_hits = reaches(bat1, lambda p: p[0] in ("F1", "Q1", "Q2", "R_F1"))
    add(
        "Harness",
        "TOP CELL",
        "J_BAT1.1 named CELL32, copper to the fuse",
        "copper" if top == "CELL32" and any(p[0] == "F1" for p in top_hits) else ("named" if top == "CELL32" else "missing"),
        f"J_BAT1.1 = {top or 'none'}" + (f" · island also {fmt_refs(top_hits)}" if top_hits else " · island is only this pad"),
        "" if top == "CELL32" else "Pack positive is not named CELL32.",
    )
    add(
        "Harness",
        "BOT",
        "J_BAT1.2 named CELL0",
        "ok" if bot == "CELL0" else "missing",
        f"J_BAT1.2 = {bot or 'none'}",
    )

    chg_p = net_of(pad("J_CHG1", "1")) if pad("J_CHG1", "1") else ""
    chg_n = net_of(pad("J_CHG1", "2")) if pad("J_CHG1", "2") else ""
    chg_hits = reaches(pad("J_CHG1", "1"), lambda p: p[0] in ("Q1", "Q2"))
    add(
        "Harness",
        "Charger XT30",
        "J_CHG1 = CHG+ / CHG−, copper to the charge FET",
        "copper" if chg_p == "CHG+" and chg_n == "CHG-" and chg_hits else ("named" if chg_p == "CHG+" and chg_n == "CHG-" else "missing"),
        f"pad1={chg_p or 'none'}, pad2={chg_n or 'none'}" + ("" if chg_hits else " · no copper to a FET"),
    )

    cell_named = 0
    cell_to_rf = 0
    cell_missing = []
    for n in range(0, 33):
        name = f"CELL{n}"
        members = pads_by_net.get(name, [])
        on_conn = [m for m in members if m[0] in CELL_CONNS]
        on_rf = [m for m in members if m[0].startswith("R_F")]
        if on_conn:
            cell_named += 1
        else:
            cell_missing.append(name)
            continue
        if not on_rf and n == 0:
            continue
        # copper island from the connector pad
        ref, num = on_conn[0]
        src = pad(ref, num)
        if reaches(src, lambda p, _rf=on_rf: (p[0], p[1]) in _rf):
            cell_to_rf += 1
    add(
        "Harness",
        "Cell taps",
        "33 sense pads named CELL32…CELL0",
        "ok" if cell_named == 33 else ("partial" if cell_named else "missing"),
        f"{cell_named} / 33 named" + (f" · missing {', '.join(cell_missing[:6])}" if cell_missing else ""),
    )
    add(
        "Harness",
        "Cell wire to filter R",
        "Each CELL1–CELL32 pad shares copper with its R_F",
        "copper" if cell_to_rf == 32 else ("partial" if cell_to_rf else "missing"),
        f"{cell_to_rf} / 32 cell nets reach an R_F pad",
        "CELL0 has no series resistor on this board.",
    )

    temp_ok = 0
    temp_copper = 0
    for i, ref in enumerate(("J_T1", "J_T2", "J_T3", "J_T4"), start=1):
        p1, p2 = pad(ref, "1"), pad(ref, "2")
        if p1 and net_of(p1) == f"TS{i}" and p2 and net_of(p2) == "GND":
            temp_ok += 1
        if p1 and reaches(p1, lambda p: p[0] in ("U_BQ1", "U_BQ2")):
            temp_copper += 1
    add(
        "Harness",
        "Temp 1–4",
        "J_T pad1 = TS1…TS4, pad2 = GND, copper to a BQ pin",
        "copper" if temp_copper == 4 else ("named" if temp_ok == 4 else ("partial" if temp_ok else "missing")),
        f"{temp_ok} / 4 named · {temp_copper} / 4 reach a BQ pin",
    )

    comm = {str(i): net_of(pad("J_COMM1", str(i))) if pad("J_COMM1", str(i)) else "" for i in range(1, 5)}
    u7 = {str(n): net_of(pad("U7", str(n))) if pad("U7", str(n)) else "" for n in (6, 7, 5, 8)}
    can_named = comm == {"1": "CANH", "2": "CANL", "3": "ISO_GND", "4": "5VExt"} and u7.get("7") == "CANH" and u7.get("6") == "CANL"
    can_copper = reaches(pad("J_COMM1", "1"), lambda p: p[0] == "U7")
    add(
        "Harness",
        "ESC CAN / 5V",
        "J_COMM1 and the isolator share CANH, CANL, ISO_GND, 5VExt in copper",
        "copper" if can_named and can_copper else ("named" if can_named else "missing"),
        "names match on J_COMM1 and U7" if can_named else f"J_COMM1={comm}",
        "" if can_copper else "No track joins the connector to U7.",
    )

    buzz = fps.get("BZ1")
    buzz_nets = []
    buzz_driven = False
    if buzz:
        for p in buzz.Pads():
            if net_of(p):
                buzz_nets.append(f"{p.GetNumber()}={net_of(p)}")
            if reaches(p, lambda q: q[0] not in ("BZ1",)):
                buzz_driven = True
    add(
        "Harness",
        "Internal buzzer",
        "BZ1 driven by another part",
        "copper" if buzz_driven else ("named" if buzz_nets else "missing"),
        ", ".join(buzz_nets) if buzz_nets else "BZ1 missing",
        "" if buzz_driven else "BUZZ_LOW does not reach another footprint.",
    )

    enable_refs = []
    for fp in board.GetFootprints():
        blob = f"{fp.GetReference()} {fp.GetValue()}".lower()
        if any(w in blob for w in ("button", "enable", "sw_push")) or fp.GetReference().upper().startswith(("SW", "BTN")):
            enable_refs.append(fp.GetReference())
    add(
        "Harness",
        "Enable override",
        "A switch footprint, netted",
        "missing",
        "no switch footprint on the board" if not enable_refs else ", ".join(enable_refs),
    )

    usb = fps.get("J_USB1")
    usb_nets = 0
    if usb:
        usb_nets = sum(1 for p in usb.Pads() if net_of(p) and is_signal(p))
    add(
        "Harness",
        "USB-C",
        "J_USB1 D+/D− and power netted to the ESP",
        "named" if usb_nets else "missing",
        f"{usb_nets} signal pads have a net" if usb else "J_USB1 missing",
    )

    # --- power path behind the connectors ---
    f1a, f1b = pad("F1", "1"), pad("F1", "2")
    fuse_named = bool(f1a and f1b and net_of(f1a) and net_of(f1b) and net_of(f1a) != net_of(f1b))
    fuse_copper = bool(f1a and f1b and reaches(f1a, lambda p: p[0] == "F1" and p[1] == "2"))
    fet_on_fuse = bool(f1b and reaches(f1b, lambda p: p[0] in ("Q1", "Q2")))
    add(
        "Power",
        "Pack fuse",
        "F1 in series, copper from CELL32 to both FET drains",
        "copper" if fuse_copper and fet_on_fuse else ("named" if fuse_named else "missing"),
        f"F1.1={net_of(f1a) if f1a else 'none'}, F1.2={net_of(f1b) if f1b else 'none'}",
        "" if fet_on_fuse else "FET drains are not on the fuse copper.",
    )

    q2g = pad("Q2", "4")
    q2g_hits = reaches(q2g, lambda p: p[0] != "Q2") if q2g else []
    add(
        "Power",
        "Discharge FET gate",
        "Q2 gate reaches a driver",
        "copper" if q2g_hits else ("named" if q2g and net_of(q2g) else "missing"),
        f"Q2.4={net_of(q2g) if q2g else 'none'}" + (f" · {fmt_refs(q2g_hits)}" if q2g_hits else " · nothing else on this island"),
    )

    q1g = pad("Q1", "4")
    q1_parts = reaches(q1g, lambda p: p[0] != "Q1") if q1g else []
    add(
        "Power",
        "Charge FET gate",
        "Q1 gate copper to the SSR output and the gate parts",
        "copper" if any(p[0] == "U_SSR1" for p in q1_parts) else ("named" if q1g and net_of(q1g) else "missing"),
        f"Q1.4={net_of(q1g) if q1g else 'none'}" + (f" · island {fmt_refs(q1_parts)}" if q1_parts else " · nothing else on this island"),
    )

    def shunt_to_sense(pad_obj):
        if not pad_obj:
            return []
        hits = []
        for ref, num, _n in cluster(pad_obj):
            if ref in ("U_BQ1", "U_BQ2") and num.isdigit() and BQ_FUNC.get(int(num)) in ("SRP", "SRN"):
                hits.append((ref, num, _n))
        return hits

    sense_hits = []
    for refn, num in (("R_SH1", "1"), ("R_SH1", "2"), ("R_SH2", "1"), ("R_SH2", "2")):
        sense_hits.extend(shunt_to_sense(pad(refn, num)))
    shunt_nets = []
    for refn, num in (("R_SH1", "1"), ("R_SH1", "2"), ("R_SH2", "2")):
        p = pad(refn, num)
        shunt_nets.append(f"{refn}.{num}={net_of(p) if p else 'none'}")
    add(
        "Power",
        "Current shunt",
        "R_SH copper to BQ SRP and SRN",
        "copper" if sense_hits else ("named" if pad("R_SH1", "1") and net_of(pad("R_SH1", "1")) else "missing"),
        " · ".join(shunt_nets),
        "" if sense_hits else "SRP/SRN stay on the BQ pins. They do not touch the shunt.",
    )

    esp = fps.get("U_ESP1")
    esp_nets = 0
    if esp:
        esp_nets = len({net_of(p) for p in esp.Pads() if net_of(p)})
    add(
        "Host",
        "ESP32-C3",
        "I2C and the buzzer/USB nets land on U_ESP1",
        "named" if esp_nets else "missing",
        f"{esp_nets} nets" if esp else "U_ESP1 missing",
    )

    buck_refs = ("U4", "L1", "D_BST1", "C_TAN1", "C_FLT1")
    buck_netted = 0
    for refn in buck_refs:
        fp = fps.get(refn)
        if fp and any(net_of(p) for p in fp.Pads()):
            buck_netted += 1
    add(
        "Host",
        "3V3 buck",
        "LTC7138 and its power parts netted",
        "named" if buck_netted == len(buck_refs) else ("partial" if buck_netted else "missing"),
        f"{buck_netted} / {len(buck_refs)} parts have a net",
    )

    # --- BQ pins ---
    def bq_pin_row(ref, number, func):
        p = pad(ref, number)
        if p is None:
            return {"ref": ref, "pin": number, "func": func, "net": "", "state": "missing", "reaches": ""}
        name = net_of(p)
        others = [q for q in cluster(p) if q[0] != ref]
        if func == "NC" and not name:
            state = "nc"
        elif not name:
            state = "empty"
        elif others:
            state = "copper"
        else:
            state = "named"
        return {
            "ref": ref,
            "pin": number,
            "func": func,
            "net": name,
            "state": state,
            "reaches": fmt_refs(others),
        }

    pins = [bq_pin_row(ref, n, func) for ref in ("U_BQ1", "U_BQ2") for n, func in BQ_PINS]

    def pin_state(ref, number):
        for row in pins:
            if row["ref"] == ref and row["pin"] == number:
                return row
        return None

    # filter resistors
    rf_ok = rf_copper = rf_present = 0
    for k in range(1, 33):
        fp = fps.get(f"R_F{k}")
        if not fp:
            continue
        rf_present += 1
        cell_n = 33 - k
        vc = f"BQ1_VC{cell_n}" if cell_n <= 16 else f"BQ2_VC{cell_n - 16}"
        nets = {net_of(p) for p in fp.Pads()}
        if f"CELL{cell_n}" in nets and vc in nets:
            rf_ok += 1
        bq_ref = "U_BQ1" if cell_n <= 16 else "U_BQ2"
        vc_pad = None
        for p in fp.Pads():
            if net_of(p) == vc:
                vc_pad = p
        if vc_pad and reaches(vc_pad, lambda q, bq=bq_ref: q[0] == bq):
            rf_copper += 1

    cf_ok = cf_copper = cf_present = 0
    for k in range(1, 33):
        fp = fps.get(f"C_F{k}")
        if not fp:
            continue
        cf_present += 1
        nets = [net_of(p) for p in fp.Pads() if net_of(p)]
        if len(set(nets)) >= 2:
            cf_ok += 1
        for p in fp.Pads():
            if reaches(p, lambda q: q[0] in ("U_BQ1", "U_BQ2")):
                cf_copper += 1
                break

    rb_netted = sum(1 for i in range(1, 34) if fps.get(f"R_B{i}") and any(net_of(p) for p in fps[f"R_B{i}"].Pads()))

    def both_empty(numbers):
        return all(pin_state(ref, n)["state"] == "empty" for ref in ("U_BQ1", "U_BQ2") for n in numbers)

    bat_short = []
    for ref in ("U_BQ1", "U_BQ2"):
        bat = pin_state(ref, 47)
        vc16 = pin_state(ref, 48)
        if bat and vc16 and bat["net"] and bat["net"] == vc16["net"]:
            bat_short.append(ref)

    blocks = [
        {
            "id": "series-r",
            "title": "Cell series 20 Ω",
            "state": "copper" if rf_copper == 32 else ("partial" if rf_ok else "missing"),
            "detail": f"{rf_present} parts placed, {rf_ok} / 32 have CELL and VC nets, {rf_copper} / 32 reach a BQ pad.",
        },
        {
            "id": "diff-c",
            "title": "Cell 0.22 µF",
            "state": "copper" if cf_copper == 32 else ("partial" if cf_ok else "missing"),
            "detail": f"{cf_present} parts placed, {cf_ok} / 32 have two nets, {cf_copper} / 32 reach a BQ pad.",
        },
        {
            "id": "vc0",
            "title": "VC0 series resistor",
            "state": "wrong" if pin_state("U_BQ1", 16)["net"] == "CELL0" else "missing",
            "detail": "U_BQ1 pin 16 (VC0) is tied straight to CELL0. The EVM uses 20 Ω there too.",
        },
        {
            "id": "bat",
            "title": "BAT pin filter",
            "state": "wrong" if bat_short else "missing",
            "detail": (
                f"{', '.join(bat_short)} pin 47 (BAT) is the same net as pin 48 (VC16). The EVM feeds BAT through its own resistor and cap."
                if bat_short else "BAT pin is open."
            ),
        },
        {
            "id": "cp1",
            "title": "CP1 charge-pump cap",
            "state": "missing" if both_empty((46,)) else "partial",
            "detail": "Pin 46 is empty on both chips.",
        },
        {
            "id": "regs",
            "title": "REG18 / REG1 / REG2 / REGIN / BREG",
            "state": "missing" if both_empty(REG_PINS) else "partial",
            "detail": "Pins 24, 34, 35, 36, and 37 are empty. Those caps are how the chip powers itself.",
        },
        {
            "id": "sense",
            "title": "SRP / SRN to the shunt",
            "state": "copper" if sense_hits else "partial",
            "detail": "Shunt pads share copper with a BQ SRP or SRN pin." if sense_hits else "Both chips have SRP and SRN net names. Those nets do not reach R_SH1 or R_SH2.",
        },
        {
            "id": "ts",
            "title": "Thermistor bias",
            "state": "partial" if temp_ok == 4 else "missing",
            "detail": f"{temp_ok} / 4 connectors are named. No 10 kΩ bias to REG18, and {temp_copper} / 4 have copper to a BQ pin.",
        },
        {
            "id": "i2c",
            "title": "I2C to the ESP",
            "state": "missing" if both_empty((26, 27)) and esp_nets == 0 else "partial",
            "detail": "SCL and SDA (pins 26 and 27) are empty. U_ESP1 has no nets.",
        },
        {
            "id": "drivers",
            "title": "BQ CHG / DSG / PCHG pins",
            "state": "missing" if both_empty(DRIVER_PINS) else "partial",
            "detail": "Pins 39, 40, 43, and 45 are empty. The charge-gate parts around Q1 are a separate named island, not these pins.",
        },
        {
            "id": "balance",
            "title": "Balance resistors R_B",
            "state": "partial" if rb_netted else "missing",
            "detail": f"{rb_netted} / 33 of the 27 Ω bleed resistors have a net. The EVM balances inside the BQ, through the VC pins.",
        },
    ]

    named_pins = {ref: sum(1 for row in pins if row["ref"] == ref and row["state"] in ("named", "copper")) for ref in ("U_BQ1", "U_BQ2")}
    copper_pins = {ref: sum(1 for row in pins if row["ref"] == ref and row["state"] == "copper") for ref in ("U_BQ1", "U_BQ2")}
    empty_pins = {ref: sum(1 for row in pins if row["ref"] == ref and row["state"] == "empty") for ref in ("U_BQ1", "U_BQ2")}

    blank = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        if any(net_of(p) for p in fp.Pads()):
            continue
        blank.append({"ref": fp.GetReference(), "value": fp.GetValue()})

    harness_rows = [r for r in rows if r["group"] == "Harness"]
    verdict = (
        f"{cell_to_rf} of 32 cell taps share copper with a filter resistor, and {rf_copper} of those resistors reach a BQ pad. "
        f"U_BQ1 has {named_pins['U_BQ1']} of 48 pins named. U_BQ2 has {named_pins['U_BQ2']}. "
        f"Copper from a BQ pin to another part: {copper_pins['U_BQ1']} and {copper_pins['U_BQ2']}. "
        f"The regulator, I2C, and FET-driver pins are empty."
    )

    try:
        unconn = int(conn.GetUnconnectedCount(False))
    except Exception:
        unconn = None

    payload = {
        "board": sys.argv[1],
        "verdict": verdict,
        "summary": {
            "footprints": len(fps),
            "pads": total_pads,
            "signal_pads_unnetted": unnetted,
            "tracks": n_trk,
            "vias": n_via,
            "unconnected": unconn,
            "bq_named": named_pins,
            "bq_copper": copper_pins,
            "bq_empty": empty_pins,
            "cell_named": cell_named,
            "cell_to_rf": cell_to_rf,
            "rf_to_bq": rf_copper,
            "blocks_copper": sum(1 for b in blocks if b["state"] == "copper"),
            "blocks_partial": sum(1 for b in blocks if b["state"] in ("partial", "wrong")),
            "blocks_missing": sum(1 for b in blocks if b["state"] == "missing"),
            "harness_copper": sum(1 for r in harness_rows if r["state"] == "copper"),
            "harness_total": len(harness_rows),
        },
        "rows": rows,
        "blocks": blocks,
        "pins": pins,
        "blank": blank,
    }
    print("@@JSON@@")
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
