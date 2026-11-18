"""Teach Freerouting the voltage-bank spacing: split each DSN net class by bank and add
class_class rules (0.6 mm) between banks two or more apart. Same banks as the .kicad_dru.
Edits only the (class ...) blocks as text (the DSN header has a bare " token).

  python dsn_banks.py rev-a/route/qfbms-rev-a.dsn
"""
import re
import sys
from pathlib import Path

from set_rules import level

CLEAR_UM = 600


def block_end(text, i):
    depth = 0
    for j in range(i, len(text)):
        c = text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j + 1
    raise ValueError("unbalanced")


def main(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    spans, new, banks_of = [], [], {}
    for m in re.finditer(r"\(class ", text):
        start, end = m.start(), block_end(text, m.start())
        blk = text[start:end]
        inner = blk[len("(class "):-1]
        first_paren = inner.find("(")
        head, tail = (inner[:first_paren], inner[first_paren:]) if first_paren >= 0 else (inner, "")
        toks = head.split()
        name, nets = toks[0], toks[1:]
        groups = {}
        for n in nets:
            groups.setdefault(level(n.strip('"')) // 4, []).append(n)
        for b, members in sorted(groups.items()):
            cname = f"{name}_b{b}"
            banks_of[cname] = b
            new.append(f"(class {cname} {' '.join(members)}\n      {tail.strip()})")
        spans.append((start, end))
    if not spans:
        raise SystemExit("no classes found")
    names = sorted(banks_of)
    rules = [f"(class_class (classes {a} {b}) (rule (clearance {CLEAR_UM})))"
             for i, a in enumerate(names) for b in names[i + 1:] if abs(banks_of[a] - banks_of[b]) >= 2]
    out = text[:spans[0][0]] + "\n    ".join(new + rules)
    prev = spans[0][1]
    for s, e in spans[1:]:
        out += text[prev:s].strip(" \t") if text[prev:s].strip() else ""
        prev = e
    out += text[prev:]
    path.write_text(out, encoding="utf-8")
    print(f"{len(new)} classes, {len(rules)} class_class rules")


if __name__ == "__main__":
    main(sys.argv[1])
