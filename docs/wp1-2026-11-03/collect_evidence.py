import pcbnew,json,hashlib,pathlib,sys,xml.etree.ElementTree as ET,collections
root=pathlib.Path.cwd(); out=root/'docs/wp1-2026-11-03'
sys.path.insert(0,str(root/'_tools/pcb_dashboard')); import kicad_bridge as bridge
files=sorted(set(list(root.glob('*.kicad_pcb'))+list(root.glob('*.kicad_sch'))+list(root.glob('*.kicad_pro'))+list(root.glob('*lib-table'))+list((root/'qfbms.pretty').rglob('*'))+list((root/'_reference/firmware').rglob('*'))+list((root/'3dmodels').rglob('*'))))
def save(n,x): (out/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
manifest=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files if p.is_file()]
if not (out/'baseline-hashes.json').exists(): save('baseline-hashes.json',manifest)
else: save('hash-verification.json',{'unchanged':json.loads((out/'baseline-hashes.json').read_text())==manifest})
b=pcbnew.LoadBoard(str(root/'qfbms32.kicad_pcb')); bd=bridge.read_board(str(root/'qfbms32.kicad_pcb')); save('live-board.json',bd)
fixed=[f for f in bd['footprints'] if f['ref'].startswith(('J','R_B'))]; save('fixed-placement.json',fixed)
old=json.loads((root/'exports/planning-2026-11-03/pad-inventory.json').read_text()); dif=[]
for f in bd['footprints']:
 o=next(x for x in old if x['ref']==f['ref']); n={p['num']:p['net'] for p in f['pads']}
 if o['pads']!=n or o['xy']!=[f['x'],f['y']] or o['rotation']!=f['rot']: dif.append({'ref':f['ref'],'old':o,'new':f})
save('prior-inventory-comparison.json',dif)
xml=ET.parse(out/'schematic.xml'); nets={}
for net in xml.findall('./nets/net'):
 for node in net.findall('node'): nets[(node.get('ref'),node.get('pin'))]={'schematic_net':net.get('name'),'symbol_pin_function':node.get('pinfunction'),'symbol_pin_type':node.get('pintype')}
ledger=[]
for f in bd['footprints']:
 for p in f['pads']:
  r={'ref':f['ref'],'value':f['value'],'footprint':f['fpid'],**p,**nets.get((f['ref'],p['num']),{})}
  r['owner']='WP2 electrical schematic'; r['source']='live pcbnew + regenerated KiCad XML; symbol function is not manufacturer verification'
  r['disposition']='unassigned: define or intentional NC required' if not p['net'] else 'assigned: reconcile schematic and manufacturer pin function'
  r['domain']='upper candidate: CELL16 local reference required' if f['ref']=='U_BQ2' or p['net'].startswith('BQ2_') else 'infer only from intended circuit; net label not proof'
  ledger.append(r)
save('pin-ledger.json',ledger)
objects={}
for f in b.GetFootprints():
 for p in f.Pads(): objects[p.m_Uuid.AsString()]={'kind':'pad','ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetname(),'xy':bridge.pt(p.GetPosition()),'layers':p.GetLayerSet().FmtBin()}
for t in b.GetTracks(): objects[t.m_Uuid.AsString()]={'kind':'via' if isinstance(t,pcbnew.PCB_VIA) else 'track','net':t.GetNetname(),'start':bridge.pt(t.GetStart()),'end':bridge.pt(t.GetEnd()),'layer':b.GetLayerName(t.GetLayer())}
drc=json.loads((out/'drc.json').read_text()); triage=[]
for i,v in enumerate(drc['violations']):
 if v['type'] in ['shorting_items','tracks_crossing']:
  obs=[objects.get(x['uuid'],{'kind':'other','uuid':x['uuid']}) for x in v['items']]
  triage.append({'id':i,'type':v['type'],'description':v['description'],'reported_items':v['items'],'objects':obs,'classification':'/'.join(sorted(x['kind'] for x in obs)),'nets':sorted(set(x.get('net','') for x in obs)),'action':'WP4 define intended nets, WP5 remove/reroute offending copper; preserve fixed pads'})
save('short-crossing-triage.json',triage)
prev=json.loads((root/'exports/planning-2026-11-03/drc.json').read_text())
key=lambda v:(v['type'],v['description'],tuple(x['uuid'] for x in v['items']))
save('report-comparison.json',{'current_counts':{k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},'types':dict(collections.Counter(x['type'] for x in drc['violations'])),'added':[v for v in drc['violations'] if key(v) not in {key(x) for x in prev['violations']}],'removed':[v for v in prev['violations'] if key(v) not in {key(x) for x in drc['violations']}],'ignored':drc['ignored_checks']})
pr=json.loads((root/'qfbms32.kicad_pro').read_text());save('project-rules.json',pr)
save('component-ledger.json',[{'ref':f['ref'],'value':f['value'],'footprint':f['fpid'],'mpn':f['mpn'],'lcsc':f['lcsc'],'status':'Requires manufacturer comparison or exact purchased MPN; value alone does not establish ratings','owner':'WP2 BOM'} for f in bd['footprints']])
print('footprints',len(bd['footprints']),'pad instances',len(ledger),'fixed footprints',len(fixed),'prior inventory differences',len(dif),'short/crossing reports',len(triage))
print([(f['ref'],f['value'],f['fpid']) for f in bd['footprints'] if not f['ref'].startswith(('R_B','R_F','C_F'))])
