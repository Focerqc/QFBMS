"""Snapshot assigned endpoints and physical copper contacts separately. Run at repo root with KiCad Python."""
import json,sys
from pathlib import Path
import pcbnew as k
out=Path(__file__).resolve().parent
root=out.parents[1]
b=k.LoadBoard(sys.argv[1])
uid=lambda i:i.m_Uuid.AsString()
xy=lambda p:[p.x/1e6,p.y/1e6]
tracks=list(b.GetTracks())
graphics=[g for g in b.GetDrawings() if isinstance(g,k.PCB_SHAPE) and k.IsCopperLayer(g.GetLayer())]
layers=list(b.GetEnabledLayers().CuStack())
objects={uid(t):dict(kind='via' if isinstance(t,k.PCB_VIA) else 'track',net=t.GetNetname(),
    start=xy(t.GetStart()),end=xy(t.GetEnd()),layers=[b.GetLayerName(l) for l in layers if t.IsOnLayer(l)]) for t in tracks}
for g in graphics:
 objects[uid(g)]=dict(kind='copper graphic',net=g.GetNetname(),layer=b.GetLayerName(g.GetLayer()),position=xy(g.GetPosition()))
pads={}
for f in b.GetFootprints():
 for p in f.Pads():
  box=p.GetBoundingBox()
  hit=[]
  for t in tracks+graphics:
   if not box.Intersects(t.GetBoundingBox()):continue
   if any(p.IsOnLayer(l) and t.IsOnLayer(l) and p.GetEffectiveShape(l).Collide(t.GetEffectiveShape(l)) for l in layers):hit.append(uid(t))
  pads[uid(p)]=dict(ref=f.GetReference(),pin=p.GetNumber(),net=p.GetNetname(),touches=sorted(hit))
zones=[dict(uuid=uid(z),owner=owner,name=z.GetZoneName(),net=z.GetNetname(),rule_area=z.GetIsRuleArea()) for owner,zs in [('board',b.Zones())]+[(f.GetReference(),f.Zones()) for f in b.GetFootprints()] for z in zs]
Path(sys.argv[2]).write_text(json.dumps(dict(objects=objects,pads=pads,zones=zones),indent=2))
print('zones',zones)
for p in pads.values():
 if p['ref'] in ('Q2','R_DSG1'): print(p)
