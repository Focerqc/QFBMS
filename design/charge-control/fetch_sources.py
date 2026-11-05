import urllib.request, pathlib, concurrent.futures,fitz
out=pathlib.Path('docs/charge-control-2026-11-04/sources');out.mkdir(exist_ok=True)
urls={'tps3431':'https://www.ti.com/lit/ds/symlink/tps3431.pdf','adum4120':'https://www.analog.com/media/en/technical-documentation/data-sheets/ADuM4120-4120-1.pdf','ipt60r022s7':'https://www.infineon.com/assets/row/public/documents/24/49/infineon-ipt60r022s7-datasheet-en.pdf','mgj1':'https://www.murata.com/products/productdata/8807029964830/kdc-mgj1.pdf','tps3808':'https://www.ti.com/lit/ds/symlink/tps3808.pdf','sn74lvc1g74':'https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf','tlv3201':'https://www.ti.com/lit/ds/symlink/tlv3201.pdf','ina301':'https://www.ti.com/lit/ds/symlink/ina301.pdf'}
def run(kv):
 k,u=kv
 try:
  data=urllib.request.urlopen(u,timeout=40).read(); (out/(k+'.pdf')).write_bytes(data); d=fitz.open(stream=data,filetype='pdf');(out/(k+'.txt')).write_text('\n'.join('PAGE '+str(i+1)+'\n'+p.get_text() for i,p in enumerate(d)),encoding='utf8'); return k,len(data)
 except Exception as e: return k,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: print(list(ex.map(run,urls.items())))
