"""Compare complete component pin partitions; do not discard floating pins or key on label names."""
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
import json
out=Path(__file__).resolve().parent
def snapshot(path):
    xml=ET.parse(path)
    parts={c.get('ref'):(c.findtext('value'),c.findtext('footprint'),c.find('libsource').get('part')) for c in xml.findall('./components/comp')}
    declared={(c.get('ref'),p.get('num')) for c in xml.findall('./components/comp') for p in c.findall('units/unit/pins/pin')}
    pins={}
    groups=set()
    for net in xml.findall('./nets/net'):
        group=set()
        for node in net.findall('node'):
            pin=(node.get('ref'),node.get('pin'))
            assert pin in declared and pin not in pins
            pins[pin]=(node.get('pintype'),node.get('pinfunction'))
            group.add(pin)
        groups.add(frozenset(group))
    return parts,declared,pins,groups,declared-pins.keys()
def findings(path):
    j=json.loads(path.read_text())
    return Counter((v['severity'],v['type'],v['description'],tuple(sorted(i['description'] for i in v['items']))) for s in j['sheets'] for v in s['violations']),j['ignored_checks']
before=snapshot(out/'before.xml');after=snapshot(out/'monitor.xml')
assert before==after
parts,declared,pins,groups,absent=after
print(len(parts),'component identities, values and footprint assignments unchanged;',len(declared),'declared pins;',len(groups),'identical groups')
print('Singletons:',sorted(next(iter(g)) for g in groups if len(g)==1))
print('NC-typed:',sorted(p for p,v in pins.items() if 'no_connect' in (v[0] or '')))
print('Declared but absent from nets:',sorted(absent))
a,ia=findings(out/'erc-before.json');b,ib=findings(out/'erc-after.json')
print('ERC removed:',dict(a-b),'added:',dict(b-a));assert a==b and ia==ib
print('Remaining:',dict(Counter((sev,kind) for sev,kind,_,_ in b.elements())))
