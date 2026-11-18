"""Small S-expression reader/writer for KiCad 10 files.

Strings stay `Str` so they are written back quoted; bare atoms stay plain `str`.
"""


class Str(str):
    """A quoted KiCad string."""


def tokenize(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    nxt = text[j + 1]
                    buf.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            yield Str("".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()":
                j += 1
            yield text[i:j]
            i = j


def parse(text):
    stack = [[]]
    for tok in tokenize(text):
        if tok == "(" and not isinstance(tok, Str):
            stack.append([])
        elif tok == ")" and not isinstance(tok, Str):
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok)
    return stack[0][0]


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dump(node, indent=0):
    """Write a node. Short lists stay on one line; long ones nest with tabs."""
    if isinstance(node, Str):
        return quote(node)
    if not isinstance(node, list):
        return str(node)
    flat = "(" + " ".join(dump(x) for x in node) + ")"
    if len(flat) <= 100 and "\n" not in flat:
        return flat
    pad = "\t" * (indent + 1)
    head = []
    rest = []
    for x in node:
        if isinstance(x, list) or rest:
            rest.append(x)
        else:
            head.append(x)
    out = "(" + " ".join(dump(x) for x in head)
    for x in rest:
        out += "\n" + pad + dump(x, indent + 1)
    return out + "\n" + "\t" * indent + ")"


def kids(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]


def kid(node, name):
    found = kids(node, name)
    return found[0] if found else None
