"""Pin-level regression checks for the BQ bus disconnect and monitor repairs.
Run after fresh KiCad XML export: python _tools/verify_bq_repair.py exports/bq-repair.xml
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def verify(path):
    root = ET.parse(path).getroot()
    pins = {}
    members = {}
    components = {c.attrib['ref']: c for c in root.findall('./components/comp')}
    for net in root.findall('./nets/net'):
        key = net.attrib['code']
        members[key] = {(n.attrib['ref'], n.attrib['pin']) for n in net.findall('node')}
        for pin in members[key]:
            assert pin not in pins, f'duplicate node {pin}'
            pins[pin] = key
    def n(ref, pin):
        return pins[(ref, str(pin))]
    def same(*nodes):
        assert len({n(*p) for p in nodes}) == 1, f'not connected: {nodes}'
    def distinct(*nodes):
        assert len({n(*p) for p in nodes}) == len(nodes), f'short: {nodes}'
    for i, bq_pin in enumerate((21, 23, 25, 31, 28), 1):
        r, rt = f'R{26+i}', f'RT{i}'
        same(('U_BQ1', bq_pin), (r, 1))
        same((r, 2), (rt, 1))
        same((rt, 2), ('U_BQ1', 17))
        distinct((r, 1), (r, 2), (rt, 2))
        assert members[n(r, 1)] == {('U_BQ1', str(bq_pin)), (r, '1')}
        assert members[n(r, 2)] == {(r, '2'), (rt, '1')}
    assert 'SW_SDA' not in components and 'SW_SCL' not in components
    assert components['U204'].findtext('value') == 'TMUX154EDGSR'
    assert components['U204'].findtext('footprint') == 'Package_SO:TSSOP-10_3x3mm_P0.5mm'
    assert 'U205' not in components and 'R204' not in components and 'C204' not in components
    # TI TMUX154E DGS actual package pins: 2=A0, 3=A1, 4=A,
    # 5=GND, 6=B, 7=B1, 8=B0, 9=EN, 1=SEL, 10=VCC.
    same(('U_BQ1', 27), ('U204', 4))
    same(('U_BQ1', 26), ('U204', 6))
    same(('U204', 2), ('U_ISO', 2), ('R201', 1))
    same(('U204', 8), ('U_ISO', 3), ('R202', 1))
    same(('R201', 2), ('R202', 2), ('U204', 10), ('U_ISO', 1), ('C201', 2), ('C203', 2))
    same(('U204', 5), ('U_ISO', 4), ('C201', 1), ('C203', 1))
    same(('U204', 1), ('U_ISO', 4))  # SEL low selects A0/B0
    same(('U204', 9), ('R203', 1))
    same(('R203', 2), ('U204', 10), ('U_ISO', 1), ('C201', 2), ('C203', 2))
    assert members[n('U204', 3)] == {('U204', '3')}
    assert members[n('U204', 7)] == {('U204', '7')}
    same(('U_ISO', 4), ('U_BQ1', 17), ('C201', 1))
    same(('U_ISO', 8), ('U_BQ2', 35), ('C202', 2))
    same(('U_ISO', 5), ('U_BQ2', 17), ('C202', 1))
    same(*[('U_BQ2', p) for p in (17, 18, 20, 49)])
    distinct(('U_BQ1', 18), ('U_BQ1', 20), ('U_BQ2', 17), ('U_BQ1', 17))
    same(('U_ISO', 7), ('U_BQ2', 27))
    same(('U_ISO', 6), ('U_BQ2', 26))
    assert members[n('U_BQ2', 25)] == {('U_BQ2', '25')}, 'upper ALERT crossed domain'
    assert components['U_BQ2'].findtext('footprint') == 'Package_QFP:TQFP-48-1EP_7x7mm_P0.5mm_EP5x5mm_ThermalVias'
    # Names supplement pin tests: establish the physical domain references.
    named = {net.attrib['code']: net.attrib['name'] for net in root.findall('./nets/net')}
    assert named[n('U_BQ1', 17)] == 'CELL0'
    assert named[n('U_BQ2', 17)] == 'CELL16'
    assert named[n('U_ISO', 1)] == 'HOST_3V3'
    print('PASS: five temperature chains; TMUX154E signal/control pins and GPIO9 gating; ISO supplies/bypasses; upper returns, ALERT and lower sense separation.')


if __name__ == '__main__':
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('exports/bq-repair.xml'))
