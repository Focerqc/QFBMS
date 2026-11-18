"""Write simple STEP body models for rev A parts that KiCad 10 has no model for.

Each model is a few coloured prisms (planar faces only), sized from the footprint's
stated body. They are body-size placeholders, not manufacturer geometry.

  Fuse_2920_7451Metric.step  F1: 2920 SMD fuse, 7.4 x 5.1 mm body (the KiCad footprint's
                             stated size), 2.0 mm high. The part is still OPEN, so the
                             height is a generic value.
  Buzzer_5.0x5.0mm_SMD.step  BZ1: 5030 magnetic buzzer (FUET-5030 / MLT-5030), 5.0 x 5.0 x
                             3.0 mm, sound port marked on top.

Output goes to QFBMS/3dmodels. Footprints link them as ${KIPRJMOD}/../3dmodels/<name>.
Plain Python, no CAD kernel needed.

Run: python tools/make_box_models.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "3dmodels"


class Step:
    def __init__(self):
        self.lines = []
        self.n = 0

    def add(self, text):
        self.n += 1
        self.lines.append(f"#{self.n}={text};")
        return f"#{self.n}"

    def pt(self, p):
        return self.add("CARTESIAN_POINT('',(%s))" % ",".join(f"{v:.6f}" for v in p))

    def dir(self, d):
        return self.add("DIRECTION('',(%s))" % ",".join(f"{v:.6f}" for v in d))

    def axis(self, origin, normal, ref):
        return self.add(f"AXIS2_PLACEMENT_3D('',{self.pt(origin)},{self.dir(normal)},{self.dir(ref)})")


def unit(v):
    m = math.sqrt(sum(c * c for c in v))
    return tuple(c / m for c in v)


def prism(s, poly, z0, z1):
    """Solid from a convex polygon (counter-clockwise seen from +z) extruded z0..z1."""
    n = len(poly)
    vb = [s.add(f"VERTEX_POINT('',{s.pt((x, y, z0))})") for x, y in poly]
    vt = [s.add(f"VERTEX_POINT('',{s.pt((x, y, z1))})") for x, y in poly]

    def edge(a, b, pa, pb):
        d = tuple(q - p for p, q in zip(pa, pb))
        length = math.sqrt(sum(c * c for c in d))
        vec = s.add(f"VECTOR('',{s.dir(unit(d))},{length:.6f})")
        line = s.add(f"LINE('',{s.pt(pa)},{vec})")
        return s.add(f"EDGE_CURVE('',{a},{b},{line},.T.)")

    P = lambda i, z: (poly[i % n][0], poly[i % n][1], z)
    eb = [edge(vb[i], vb[(i + 1) % n], P(i, z0), P(i + 1, z0)) for i in range(n)]
    et = [edge(vt[i], vt[(i + 1) % n], P(i, z1), P(i + 1, z1)) for i in range(n)]
    ev = [edge(vb[i], vt[i], P(i, z0), P(i, z1)) for i in range(n)]

    def face(oriented, origin, normal, ref):
        oe = [s.add(f"ORIENTED_EDGE('',*,*,{e},{'.T.' if f else '.F.'})") for e, f in oriented]
        loop = s.add(f"EDGE_LOOP('',({','.join(oe)}))")
        bound = s.add(f"FACE_OUTER_BOUND('',{loop},.T.)")
        plane = s.add(f"PLANE('',{s.axis(origin, normal, ref)})")
        return s.add(f"ADVANCED_FACE('',({bound}),{plane},.T.)")

    faces = [
        face([(e, True) for e in et], P(0, z1), (0, 0, 1), (1, 0, 0)),
        face([(eb[i], False) for i in reversed(range(n))], P(0, z0), (0, 0, -1), (1, 0, 0)),
    ]
    for i in range(n):
        dx, dy = poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1]
        faces.append(face([(eb[i], True), (ev[(i + 1) % n], True), (et[i], False), (ev[i], False)],
                          P(i, z0), unit((dy, -dx, 0)), unit((dx, dy, 0))))
    shell = s.add(f"CLOSED_SHELL('',({','.join(faces)}))")
    return s.add(f"MANIFOLD_SOLID_BREP('',{shell})")


def box(x0, y0, x1, y1, z0, z1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1


def disc(cx, cy, r, z0, z1, sides=24):
    return [(cx + r * math.cos(2 * math.pi * k / sides), cy + r * math.sin(2 * math.pi * k / sides))
            for k in range(sides)], z0, z1


def write(name, parts):
    """parts: list of ((poly, z0, z1), (r, g, b))."""
    s = Step()
    app = s.add("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
    s.add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,{app})")
    pc = s.add(f"PRODUCT_CONTEXT('',{app},'mechanical')")
    prod = s.add(f"PRODUCT('{name}','{name}','',({pc}))")
    s.add(f"PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,({prod}))")
    pdf = s.add(f"PRODUCT_DEFINITION_FORMATION('','',{prod})")
    pdc = s.add(f"PRODUCT_DEFINITION_CONTEXT('part definition',{app},'design')")
    pd = s.add(f"PRODUCT_DEFINITION('design','',{pdf},{pdc})")
    pds = s.add(f"PRODUCT_DEFINITION_SHAPE('','',{pd})")
    lu = s.add("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
    au = s.add("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
    su = s.add("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
    unc = s.add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),{lu},'distance_accuracy_value','confusion accuracy')")
    ctx = s.add(f"(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(({unc}))"
                f"GLOBAL_UNIT_ASSIGNED_CONTEXT(({lu},{au},{su}))REPRESENTATION_CONTEXT('',''))")
    origin = s.axis((0, 0, 0), (0, 0, 1), (1, 0, 0))
    solids, styled = [], []
    for (poly, z0, z1), rgb in parts:
        sol = prism(s, poly, z0, z1)
        solids.append(sol)
        col = s.add("COLOUR_RGB('',%.4f,%.4f,%.4f)" % rgb)
        # Part 21 allows no inline entity instances: every style step is its own entity
        fac = s.add(f"FILL_AREA_STYLE_COLOUR('',{col})")
        fill = s.add(f"FILL_AREA_STYLE('',({fac}))")
        ssfa = s.add(f"SURFACE_STYLE_FILL_AREA({fill})")
        sss = s.add(f"SURFACE_SIDE_STYLE('',({ssfa}))")
        ssu = s.add(f"SURFACE_STYLE_USAGE(.BOTH.,{sss})")
        psa = s.add(f"PRESENTATION_STYLE_ASSIGNMENT(({ssu}))")
        styled.append(s.add(f"STYLED_ITEM('color',({psa}),{sol})"))
    rep = s.add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('{name}',({origin},{','.join(solids)}),{ctx})")
    s.add(f"SHAPE_DEFINITION_REPRESENTATION({pds},{rep})")
    s.add(f"MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({','.join(styled)}),{ctx})")
    text = "\n".join([
        "ISO-10303-21;", "HEADER;",
        f"FILE_DESCRIPTION(('{name}: body-size placeholder for QFBMS rev A'),'2;1');",
        f"FILE_NAME('{name}.step','2026-11-17T00:00:00',(''),(''),'make_box_models.py','make_box_models.py','');",
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));", "ENDSEC;", "DATA;",
        *s.lines, "ENDSEC;", "END-ISO-10303-21;", ""])
    path = OUT / f"{name}.step"
    path.write_text(text, encoding="ascii", newline="\n")
    print(f"wrote {path} ({len(parts)} solids)")


TIN = (0.82, 0.82, 0.84)
BLACK = (0.10, 0.10, 0.10)
DARK = (0.03, 0.03, 0.03)
FUSE_BODY = (0.88, 0.85, 0.74)


def main():
    OUT.mkdir(exist_ok=True)
    # 2920 fuse: 7.4 x 5.1 mm, 1.0 mm terminations each end (onto the 1.925 mm pads at +-3.39)
    L, W, H, T = 7.4, 5.1, 2.0, 1.0
    write("Fuse_2920_7451Metric", [
        (box(-L / 2, -W / 2, -L / 2 + T, W / 2, 0, H), TIN),
        (box(-L / 2 + T, -W / 2 + 0.05, L / 2 - T, W / 2 - 0.05, 0.05, H - 0.05), FUSE_BODY),
        (box(L / 2 - T, -W / 2, L / 2, W / 2, 0, H), TIN),
    ])
    # 5030 buzzer: 5.0 x 5.0 x 3.0 mm black body, 1.6 mm sound port on top, terminal tabs
    # under pads 1-3 (body edge at +-2.5) so it reads as soldered in the render
    write("Buzzer_5.0x5.0mm_SMD", [
        (box(-2.5, -2.5, 2.5, 2.5, 0.1, 3.0), BLACK),
        (disc(0, 0, 0.8, 3.0, 3.02), DARK),
        (box(1.35, -2.4, 2.55, -1.0, 0, 0.1), TIN),
        (box(1.4, 1.0, 2.55, 2.4, 0, 0.1), TIN),
        (box(-2.55, 1.0, -1.4, 2.4, 0, 0.1), TIN),
    ])


if __name__ == "__main__":
    main()
