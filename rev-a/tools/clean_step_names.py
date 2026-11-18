"""Shorten STEP product names so MCAD tools can use them as file names.

SolidWorks saves every STEP product as <name>.SLDPRT. The Espressif ESP32-C3-MINI-1 model
has product names up to 177 characters with ^ and ( ), which SolidWorks rejects as an
invalid path once its folder is added. This rewrites each PRODUCT's id and name to a short,
plain name (the part before any ^, other characters replaced by _, at most MAXLEN
characters). Distinct original names stay distinct, so no two parts share a file.
Geometry is untouched.

Run: python tools/clean_step_names.py ../3dmodels/ESP32-C3-MINI-1.STEP
"""
import re
import sys
from pathlib import Path

MAXLEN = 48
PRODUCT = re.compile(r"PRODUCT\s*\(\s*'([^']*)'\s*,\s*'([^']*)'")


def short(name):
    s = re.sub(r"\s+", "", name).split("^")[0]
    s = re.sub(r"[^A-Za-z0-9_.\-]", "_", s).strip("_.") or "part"
    return s[:MAXLEN]


def clean(path):
    text = path.read_bytes().decode("latin-1")   # bytes: keep the file's line endings
    new_of, used = {}, set()

    def rename(old):
        if old not in new_of:
            base = cand = short(old)
            k = 2
            while cand.lower() in used:
                cand = f"{base[:MAXLEN - 4]}_{k}"
                k += 1
            used.add(cand.lower())
            new_of[old] = cand
        return new_of[old]

    def sub(m):
        return f"PRODUCT('{rename(m.group(1))}','{rename(m.group(2))}'"

    out, n = PRODUCT.subn(sub, text)
    changed = sum(1 for a, b in new_of.items() if a != b)
    path.write_bytes(out.encode("latin-1"))
    print(f"{path.name}: {n} products, {changed} names shortened, longest now "
          f"{max(map(len, new_of.values()))}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        clean(Path(p))
