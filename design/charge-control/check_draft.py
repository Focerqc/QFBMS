import json,xml.etree.ElementTree as E
from pathlib import Path
import pymupdf
p=Path('design/charge-control');r=E.parse(p/'netlist.xml').getroot();got={}
for n in r.findall('./nets/net'):
 for node in n.findall('node'):got[node.attrib['ref']+'.'+node.attrib['pin']]=n.attrib['name'].lstrip('/')
exp=json.loads((p/'expected-connectivity.json').read_text());bad=[(k,v,got.get(k)) for k,v in exp.items() if got.get(k)!=v]
print('Components',len(r.findall('./components/comp')),'Pins',len(got),'expected',len(exp),'mismatches',len(bad));print(bad[:12])
for f in (p/'render').glob('*.svg'):
 d=pymupdf.open(f);a=pymupdf.open('pdf',d.convert_to_pdf());a[0].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(f.with_suffix('.png'))
