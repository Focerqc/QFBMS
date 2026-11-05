import pcbnew,json,hashlib
from pathlib import Path
p=Path('qfbms32.kicad_pcb'); b=pcbnew.LoadBoard(str(p)); rows=[]
for f in b.GetFootprints():
 rows.append(dict(ref=f.GetReference(),value=f.GetValue(),footprint=str(f.GetFPID().GetUniStringLibId()),uuid=f.m_Uuid.AsString(),xy=[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],angle=f.GetOrientationDegrees(),pads=[dict(pin=p.GetNumber(),net=p.GetNetname(),xy=[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],size=[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)]) for p in f.Pads()]))
Path('docs/charge-control-2026-11-04/live-board.json').write_text(json.dumps(rows,indent=2))
paths=[p for p in Path('.').rglob('*') if p.is_file() and (p.suffix in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_mod'] or str(p).startswith('_reference\\firmware') or str(p).startswith('firmware\\') or str(p) in ['PLAN.md','docs\\review-reconcile-2026-11-04\\README.md']) and '.git' not in p.parts]
Path('docs/charge-control-2026-11-04/baseline-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
for r in rows:
 if r['ref'] in ['Q1','Q2','F1','U_SSR1','R_SH1','R_SH2'] or r['ref'].startswith('J_CH'): print(json.dumps(r))
