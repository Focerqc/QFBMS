import sys, numpy as np
from PIL import Image
S=sys.argv[1]; out=sys.argv[2]
r=Image.open(sys.argv[3] if len(sys.argv)>3 else f'{S}/render_crop.png').convert('RGBA')
RC=[tuple(map(int,v.split(','))) for v in sys.argv[4].split(';')] if len(sys.argv)>4 else [(77,61),(2970,61),(2970,773),(77,773)]
def coeffs(dst,src):
    A=[];B=[]
    for (x,y),(u,v) in zip(dst,src):
        A+=[[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]; B+=[u,v]
    return np.linalg.solve(np.array(A,float),np.array(B,float)).tolist()
def warp(photo,dst):
    return r.transform(photo.size,Image.PERSPECTIVE,coeffs(dst,RC),Image.BICUBIC)
jobs=[('photo', f'{S}/photo.webp', [(47,250),(998,244),(1002,478),(47,482)], (0,0,0), (0,190,1024,540)),
      ('wiring','_reference/vfbms32_wiring_32s_best.jpg',[(814,178),(814,892),(638,892),(638,178)],(255,255,255),None)]
for name,path,dst,bg,crop in jobs:
    p=Image.open(path).convert('RGBA'); w=warp(p,dst)
    top=Image.new('RGBA',p.size,bg+(255,)); top.alpha_composite(w)
    ov=p.copy(); half=w.copy(); half.putalpha(w.getchannel('A').point(lambda a:int(a*0.5))); ov.alpha_composite(half)
    if crop: top,pc,ov=top.crop(crop),p.crop(crop),ov.crop(crop)
    else: pc=p
    if name=='wiring':
        # vertical board: put render beside the diagram, cropped to the board column band
        band=(560,140,900,940); a,b=top.crop(band),pc.crop(band)
        st=Image.new('RGBA',(a.width*2+20,a.height),(255,255,255,255)); st.paste(a,(0,0)); st.paste(b,(a.width+20,0))
        full=Image.new('RGBA',(pc.width,pc.height*2+20),(255,255,255,255)); full.paste(top,(0,0)); full.paste(pc,(0,pc.height+20))
        full.convert('RGB').save(f'{out}/{name}_render_above.png'); st.convert('RGB').save(f'{out}/{name}_render_beside_zoom.png')
    else:
        full=Image.new('RGBA',(pc.width,pc.height*2+10),(40,40,40,255)); full.paste(top,(0,0)); full.paste(pc,(0,pc.height+10))
        full.convert('RGB').save(f'{out}/{name}_render_above.png')
    ov.convert('RGB').save(f'{out}/{name}_overlay.png')
