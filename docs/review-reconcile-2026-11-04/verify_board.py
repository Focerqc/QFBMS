"""Compare reviewed snapshots against the live board. Run from repo root with KiCad Python."""
import collections,hashlib,json,re,sys
from pathlib import Path
out=Path(__file__).resolve().parent
root=out.parents[1]
sys.path.insert(0,str(root/'_tools/pcb_dashboard'))
from kicad_bridge import read_board
read=lambda n:json.loads((out/n).read_text())
b=read_board(str(root/'qfbms32.kicad_pcb'))
(out/'board-after.json').write_text(json.dumps(b,indent=2))
a=read('board-before.json')
idx=lambda j:{f['ref']:f for f in j['footprints']}
old,new=idx(a),idx(b)
assert old.keys()-new.keys()=={'Q2'} and new.keys()<=old.keys()
assert all(new[r]==old[r] for r in new)
assert all(b[k]==a[k] for k in ['tracks','vias','edges','bbox'])
fixed=read('protected-native-before.json');assert len(fixed)==45
native=(root/'qfbms32.kicad_pcb').read_text()
assert all(native.count(block)==1 for block in fixed.values())
c,d=map(read,['pad-copper-before.json','pad-copper-after.json'])
assert c['zones']==d['zones'] and c['objects'].keys()==d['objects'].keys()
for uid,o in c['objects'].items():
    expected=dict(o)
    if uid=='cad39c70-0b10-448b-a789-0bdbc12c340d':
        assert expected['net']==''
        expected['net']='SHUNT_MID' # effective ownership inferred by pcbnew after Q2 is absent
    assert expected==d['objects'][uid]
print('Only effective copper-net change: unchanged F.Cu polygon cad39c70 now resolves to SHUNT_MID.')
assert {k:p for k,p in c['pads'].items() if p['ref']!='Q2'}==d['pads']
hashes=read('hashes-before.json')
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in hashes.items()
           if p=='qfbms32.kicad_sch' or p.startswith(('firmware','_reference','qfbms.pretty')))
print('Footprints',len(old),'->',len(new),'; physical pads',len(c['pads']),'->',len(d['pads']))
print('Only Q2 removed. All 45 protected footprint blocks identical, 0 changed retained pad assignments.')
print('Identical copper geometry, all remaining direct pad contacts and zone:',collections.Counter(o['kind'] for o in d['objects'].values()),d['zones'])
print('Main schematic, supplied/maintained firmware and custom footprints match starting SHA-256.')
# Match physical findings by type, unordered item identities and descriptions; for parity
# compare described components/coordinates since transient KiCad IDs can vary between runs.
A,B=map(read,['drc-before.json','drc-after.json'])
delta={}
for section in ('violations','unconnected_items','schematic_parity'):
 def key(v):
  items=sorted((i['description'],i.get('pos',{}).get('x'),i.get('pos',{}).get('y'),i['uuid'] if section!='schematic_parity' else '') for i in v['items'])
  return v['type'],v['severity'],tuple(items),v['description'] if v['type']!='shorting_items' else ''
 def diff(x,y):
  rest=collections.Counter(key(v) for v in y)
  result=[]
  for v in x:
   if rest[key(v)]:rest[key(v)]-=1
   else:result.append(v)
  return result
 x,y=A[section],B[section];delta[section]={'before':len(x),'after':len(y),'added':diff(y,x),'removed':diff(x,y),'remaining_by_type':dict(collections.Counter(v['type'] for v in y))}
 print(section,len(x),'->',len(y),'added',len(delta[section]['added']),'removed',len(delta[section]['removed']))
assert A['ignored_checks']==B['ignored_checks']
(out/'drc-delta.json').write_text(json.dumps(delta,indent=2))
