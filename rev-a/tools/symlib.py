"""Load KiCad 10 library symbols, flatten `extends`, and report pin geometry."""
import copy
import os
from pathlib import Path

from sexp import Str, kid, kids, parse

KICAD_SYM_DIR = Path(os.environ.get(
    "KICAD10_SYMBOL_DIR", r"C:\Program Files\KiCad\10.0\share\kicad\symbols"))
LOCAL_LIBS = {}  # nickname -> parsed tree, registered by the generator

_cache = {}


def register_local(nickname, tree):
    LOCAL_LIBS[nickname] = tree


def _lib(nick):
    if nick in LOCAL_LIBS:
        return LOCAL_LIBS[nick]
    if nick not in _cache:
        path = KICAD_SYM_DIR / f"{nick}.kicad_sym"
        _cache[nick] = parse(path.read_text(encoding="utf-8"))
    return _cache[nick]


def _find(lib, name):
    for node in kids(lib, "symbol"):
        if node[1] == name:
            return node
    raise KeyError(name)


def flatten(lib_id):
    """Return the symbol tree named `lib_id`, with any `extends` resolved."""
    nick, name = lib_id.split(":", 1)
    lib = _lib(nick)
    sym = copy.deepcopy(_find(lib, name))
    ext = kid(sym, "extends")
    if ext:
        parent = flatten(f"{nick}:{ext[1]}")
        child_props = {p[1]: p for p in kids(sym, "property")}
        out = [x for x in parent if not (isinstance(x, list) and x[0] == "property")]
        # parent props first, overridden by child props, then any child-only props
        merged = []
        for p in kids(parent, "property"):
            merged.append(child_props.pop(p[1], p))
        merged.extend(child_props.values())
        # rebuild in KiCad's usual order: header atoms, flags, properties, units
        head = [x for x in out if not isinstance(x, list)]
        flags = [x for x in out if isinstance(x, list) and x[0] != "symbol"]
        units = [x for x in out if isinstance(x, list) and x[0] == "symbol"]
        for u in units:
            pname = parent[1].split(":")[-1]
            u[1] = Str(name + u[1][len(pname):])
        sym = head + flags + merged + units
    sym[1] = Str(lib_id)
    return sym


def pins(sym):
    """Pins of body style 1 (units 0 and 1): list of dicts."""
    out = []
    units = set()
    for sub in kids(sym, "symbol"):
        tag = sub[1]
        unit, style = tag.rsplit("_", 2)[-2:]
        if style not in ("0", "1"):
            continue
        if unit != "0":
            units.add(unit)
        for p in kids(sub, "pin"):
            at = kid(p, "at")
            out.append({
                "type": p[1],
                "x": float(at[1]),
                "y": float(at[2]),
                "angle": int(float(at[3])) % 360 if len(at) > 3 else 0,
                "length": float(kid(p, "length")[1]),
                "name": kid(p, "name")[1],
                "number": kid(p, "number")[1],
                "hidden": any(x == "hide" for x in p) or bool(kid(p, "hide")),
                "unit": unit,
            })
    return out, sorted(units)


def body_box(sym):
    """Rough body extent in library coordinates (y up)."""
    xs, ys = [], []

    def walk(node):
        if not isinstance(node, list) or not node:
            return
        if node[0] in ("start", "end", "xy", "at", "center") and len(node) >= 3:
            try:
                xs.append(float(node[1]))
                ys.append(float(node[2]))
            except ValueError:
                pass
        if node[0] == "property":
            return
        for x in node:
            walk(x)

    for sub in kids(sym, "symbol"):
        walk(sub)
    if not xs:
        return (-1.27, -1.27, 1.27, 1.27)
    return (min(xs), min(ys), max(xs), max(ys))
