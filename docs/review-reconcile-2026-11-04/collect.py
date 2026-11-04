import sys,json,hashlib,subprocess
from pathlib import Path
import pcbnew
root=Path.cwd(); out=Path(sys.argv[1]); out.mkdir(exist_ok=False,parents=True)
sys.path.insert(0,str(root/'_tools/pcb_dashboard'))
import kicad_bridge as kb
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2),encoding='utf-8')
b=pcbnew.LoadBoard(str(root/'qfbms32.kicad_pcb'))
save('board-before.json',kb.read_board(str(root/'qfbms32.kicad_pcb')))
files=[p for p in root.rglob('*') if p.is_file() and (p.parent==root and p.suffix in ('.kicad_pcb','.kicad_sch','.kicad_pro') or any(s in p.parts for s in ('firmware','qfbms32-adaptation','qfbms.pretty')))]
save('hashes-before.json',{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
git=r'C:\Program Files\Git\cmd\git.exe'
save('start.json',{a:subprocess.check_output([git,*args],text=True) for a,args in [('commit',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain=v1']),('worktrees',['worktree','list','--porcelain'])]})
# Exact native S-expressions retain geometry not exposed by dashboard approximations.
text=(root/'qfbms32.kicad_pcb').read_text()
import re
blocks=re.findall(r'\n\t\(footprint[\s\S]*?(?=\n\t\(|\n\)$)',text)
protected={}
for block in blocks:
 m=re.search(r'\(property "Reference" "([^"]+)"',block)
 if m and m[1].startswith(('J','R_B')): protected[m[1]]=block
save('protected-native-before.json',protected)
print('protected',len(protected))
for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
 print(f.GetReference(),f.GetValue(),'; '.join(p.GetNumber()+':'+p.GetNetname() for p in f.Pads()))
