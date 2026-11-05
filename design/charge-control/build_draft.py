"""New standalone schematic builder. Never reads or writes the working PCB or old schematics."""
from pathlib import Path
import uuid,json,csv,math
P=Path(__file__).resolve().parent
NS=uuid.UUID('2df37ace-e47d-42bf-8fa7-049970757c54')
def uid(s): return str(uuid.uuid5(NS,s))
def q(s): return json.dumps(str(s))
def prop(k,v,x,y,hide=False): return f'(property {q(k)} {q(v)} (at {x} {y} 0) (effects (font (size 1.1 1.1))'+(' (hide yes)' if hide else '')+'))'
LIB={}; BOM=[]; EXPECT={}
def lib(name,pins):
 # pins: number,name,electrical type; left/right placement explicit by index
 n=len(pins); h=max(5.08, math.ceil(n/2)*2.54)
 s=f'(symbol "{name}" (pin_names (offset 0.8)) (in_bom yes) (on_board yes) '+prop('Reference','U',0,h+3)+prop('Value',name,0,h+1)+f'(symbol "{name}_0_1" (rectangle (start -12.7 {h}) (end 12.7 {-h}) (stroke (width 0.254) (type default)) (fill (type background))))'
 pts={}; chunks=[]
 for i,(num,pn,typ) in enumerate(pins):
  side=i%2; y=h-2.54*(1+i//2); x=17.78 if side else -17.78; angle=180 if side else 0
  pts[str(num)]=(x,-y)
  chunks.append(f'(pin {typ} line (at {x} {y} {angle}) (length 5.08) (name {q(pn)} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 0.9 0.9)))))')
 s=s+f'(symbol "{name}_1_1" '+''.join(chunks)+'))'
 LIB[name]=(s,pts,h)
 return name
lib('R',[(1,'1','passive'),(2,'2','passive')]);lib('C',[(1,'1','passive'),(2,'2','passive')]);lib('Diode',[(1,'K','passive'),(2,'A','passive')]);lib('Fuse',[(1,'1','passive'),(2,'2','passive')]);lib('Switch',[(1,'1','passive'),(2,'2','passive')])
lib('AGM15T03LL',[(1,'G','input'),(9,'D','passive')]+[(i,'S','passive') for i in range(2,9)])
lib('TPS3431',[(1,'VDD','power_in'),(7,'WDO_N','open_collector'),(2,'CWD','passive'),(8,'ENOUT','open_collector'),(3,'EN','input'),(6,'WDI','input'),(4,'GND','power_in'),(5,'SET1','input'),(9,'EP','power_in')])
lib('TPS3808',[(6,'VDD','power_in'),(1,'RESET_N','open_collector'),(5,'SENSE','input'),(4,'CT','passive'),(3,'MR_N','input'),(2,'GND','power_in')])
lib('DFF',[(2,'D','input'),(5,'Q','output'),(1,'CLK','input'),(3,'Q_N','output'),(6,'CLR_N','input'),(7,'PRE_N','input'),(4,'GND','power_in'),(8,'VCC','power_in')])
lib('AND',[(1,'A','input'),(4,'Y','output'),(2,'B','input'),(5,'VCC','power_in'),(3,'GND','power_in')])
lib('INV',[(2,'A','input'),(4,'Y','output'),(1,'NC','no_connect'),(5,'VCC','power_in'),(3,'GND','power_in')])
lib('CMP',[(3,'IN+','input'),(1,'OUT','output'),(4,'IN-','input'),(5,'VCC','power_in'),(2,'GND','power_in')])
lib('ADUM4120',[(1,'VDD1','power_in'),(6,'VDD2','power_in'),(2,'VIN','input'),(5,'VOUT','output'),(3,'GND1','power_in'),(4,'GND2','power_in')])
lib('MGJ1',[(8,'VIN+','power_in'),(5,'+15V','power_out'),(1,'VIN-','power_in'),(6,'0V','power_out'),(2,'NA','no_connect'),(3,'-5V','power_out'),(7,'NC','no_connect'),(4,'-5V','passive')])
lib('TPS7A1601',[(8,'IN','power_in'),(1,'OUT','power_out'),(5,'EN','input'),(2,'FB','input'),(7,'DELAY','passive'),(3,'PG','open_collector'),(6,'NC','no_connect'),(4,'GND','power_in'),(9,'EP','power_in')])
lib('TLV760',[(2,'IN','power_in'),(1,'OUT','power_out'),(3,'GND','power_in')])
lib('Opto',[(1,'A','passive'),(4,'C','open_collector'),(2,'K','passive'),(3,'E','passive')])
lib('NPN',[(1,'B','input'),(3,'C','open_collector'),(2,'E','passive')])
lib('Port',[(1,'BOUNDARY','passive')]);lib('SupplyPort',[(1,'EXTERNAL_RAIL','power_out')])
class Sheet:
 def __init__(self,name,title): self.name=name;self.title=title;self.parts=[];self.used=set();self.i=0
 def text(self,x,y,s,size=1.4):self.parts.append(f'(text {q(s)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{uid(self.name+str(x)+str(y)+s)}"))')
 def part(self,ref,typ,value,mpn,nets,foot='',status='DRAFT',xy=None):
  self.used.add(typ);sym,pts,h=LIB[typ]
  if xy is None:
   col=self.i%4;row=self.i//4; x=55+col*100;y=43+row*39;self.i+=1
  else:x,y=xy
  x=round(round(x/1.27)*1.27,2);y=round(round(y/1.27)*1.27,2)
  s=f'(symbol (lib_id "Charge:{typ}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp '+('yes' if status=='DNP' else 'no')+f') (uuid "{uid(ref)}")'
  s+=prop('Reference',ref,x,y-h-5)+prop('Value',value,x,y-h-2)+prop('Footprint',foot,x,y,True)+prop('MPN',mpn,x,y,True)+prop('Status',status,x,y,True)
  for n,(dx,dy) in pts.items():
   s+=f'(pin "{n}" (uuid "{uid(ref+":"+n)}"))'
   net=nets.get(n);a=x+dx;b=y+dy
   if net is None:self.parts.append(f'(no_connect (at {a} {b}) (uuid "{uid(ref+"nc"+n)}"))')
   else:
    end=a+(5.08 if dx>0 else -5.08)
    self.parts.append(f'(wire (pts (xy {a} {b}) (xy {end} {b})) (stroke (width 0) (type default)) (uuid "{uid(ref+"w"+n)}"))')
    angle=0 if dx>0 else 180
    self.parts.append(f'(global_label {q(net)} (shape passive) (at {end} {b} {angle}) (effects (font (size 0.9 0.9)) (justify '+('left' if dx>0 else 'right')+f')) (uuid "{uid(ref+"l"+n)}"))')
    EXPECT[f'{ref}.{n}']=net
  s+=f'(instances (project "charge-control" (path "/{uid("root")}/{uid(self.name+"sheet")}" (reference "{ref}") (unit 1)))))'
  self.parts.append(s)
  if typ not in ['Port','SupplyPort']:BOM.append(dict(reference=ref,value=value,mpn=mpn,footprint=foot,status=status,sheet=self.name))
 def r(self,ref,value,a,b,mpn=None,status='DRAFT'):
  code={'10k':'1002','100k':'1003','22':'22R0','1k':'1001','2k':'2001','680':'6800','330k':'3303','10.2k':'1022','10.7k':'1072','287k':'2873','47k':'4702','0':'0R00'}[value]
  self.part(ref,'R',value,mpn or 'RC0603FR-07'+({'10k':'10K','100k':'100K','22':'22R','1k':'1K','2k':'2K','680':'680R','330k':'330K','10.2k':'10K2','10.7k':'10K7','287k':'287K','47k':'47K','0':'0R'}[value])+'L',{'1':a,'2':b},('Resistor_SMD:R_1206_3216Metric' if mpn and mpn.startswith('CRCW1206') else 'Resistor_SMD:R_0603_1608Metric'),status)
 def c(self,ref,value,a,b):
  mp={'100n':'GRM188R71H104KA93D','1n C0G 1%':'C0603C102F5GACTU','47p C0G':'GRM1885C1H470JA01D','10u 50V':'GRM32ER71H106KA12L'}[value]
  self.part(ref,'C',value,mp,{'1':a,'2':b},'Capacitor_SMD:C_1210_3225Metric' if value.startswith('10u') else 'Capacitor_SMD:C_0603_1608Metric')
 def gate(self,ref,a,b,y): self.part(ref,'AND','SN74LVC1G08DBVR','SN74LVC1G08DBVR',{'1':a,'2':b,'4':y,'3':'CELL0','5':'HOST_3V3'},'Package_TO_SOT_SMD:SOT-23-5')
 def inv(self,ref,a,y): self.part(ref,'INV','SN74LVC1G14DBVR','SN74LVC1G14DBVR',{'2':a,'4':y,'3':'CELL0','5':'HOST_3V3'},'Package_TO_SOT_SMD:SOT-23-5')
 def save(self):
  libtxt=''.join(LIB[n][0].replace(f'(symbol "{n}"',f'(symbol "Charge:{n}"',1) for n in sorted(self.used))
  # A2 provides generous grid spacing; review symbols are pin-explicit blocks.
  s=f'(kicad_sch (version 20250114) (generator "charge_control_draft") (uuid "{uid(self.name)}") (paper "A2") (title_block (title {q(self.title)}) (date "2026-11-04") (rev "DRAFT - NOT RELEASED")) (lib_symbols {libtxt}) '+''.join(self.parts)+')'
  (P/(self.name+'.kicad_sch')).write_text(s)
S=[]
def sheet(n,title,notes):
 s=Sheet(n,title);s.text(15,12,title,2);s.text(15,20,notes,1.2);S.append(s);return s
s=sheet('power','01 / Charge path - reference AGM option','Conditional AGM choice; not a qualified 150 V clamp design. See design note.\nBody diodes point COMMON_SOURCE -> each drain. No discharge/load switch is added.')
s.part('QCC1','AGM15T03LL','AGM15T03LL','AGM15T03LL',{'1':'GATE_A','9':'PACK_FUSED',**{str(i):'COMMON_SOURCE' for i in range(2,9)}},'','CONDITIONAL')
s.part('QCC2','AGM15T03LL','AGM15T03LL','AGM15T03LL',{'1':'GATE_B','9':'CHG_FUSED',**{str(i):'COMMON_SOURCE' for i in range(2,9)}},'','CONDITIONAL')
s.part('FCC1','Fuse','PACK FUSE - OPEN SELECTION','UNRESOLVED',{'1':'CELL32','2':'PACK_FUSED'},status='OPEN')
s.part('FCC2','Fuse','CHARGER FUSE - OPEN SELECTION','UNRESOLVED',{'1':'CHG_POS','2':'CHG_FUSED'},status='OPEN')
s.part('DCC1','Diode','REVERSE CROWBAR - OPEN','UNRESOLVED',{'1':'CHG_FUSED','2':'CHG_NEG'},status='OPEN')
s.part('RCC1','R','10m / fast-trip Kelvin','WSLP2512R0100FEA',{'1':'CELL0','2':'RETURN_SENSE'},'Resistor_SMD:R_2512_6332Metric','CONDITIONAL')
s.part('RCC2','R','Existing R_SH1 1m','UNRESOLVED_EXISTING',{'1':'RETURN_SENSE','2':'SHUNT_MID'},status='OPEN')
s.part('RCC3','R','Existing R_SH2 1m','UNRESOLVED_EXISTING',{'1':'SHUNT_MID','2':'CHG_NEG'},status='OPEN')
for ref,g in [('RCC4','GATE_A'),('RCC5','GATE_B')]:s.r(ref,'22','GATE_DRIVE',g)
for ref,g in [('RCC6','GATE_A'),('RCC7','GATE_B')]:s.r(ref,'10k',g,'COMMON_SOURCE')
for ref,g in [('DCC2','GATE_A'),('DCC3','GATE_B')]:s.part(ref,'Diode','PDZ16B','PDZ16B,115',{'1':g,'2':'COMMON_SOURCE'},'Diode_SMD:D_SOD-323')
for i,n in enumerate(['CELL32','CELL0','CHG_POS','CHG_NEG']):s.part('P'+str(i+1),'Port',n,'INTERFACE',{'1':n})
s.text(15,280,'FCC2 is before the reverse clamp: reverse charger current must cross it.\nFCC1 is pack-side backup. A current-limited 5 A charger may NEVER open a 10/15 A fuse.\nDCC1 must survive the complete pulse and sustained fault, not be assumed to fail short.\nNo TVS is populated: a verified clamp below 150 V at the required current remains OPEN.\nQCC2 is a proposed series charge-port blocker, not restoration of the removed legacy Q2.\nOriginal shunt Kelvin pickup/calibration is unresolved; new trip shunt is independent.',1.6)
s=sheet('driver','02 / Isolated gate drive','Selected functional-isolation supply; HOST_5V is an integration prerequisite.\nOutput stays low on driver UVLO. Secondary-good feedback clears primary permission.')
s.part('UCC1','MGJ1','MGJ1D051505MPC-R7','MGJ1D051505MPC-R7',{'8':'HOST_5V_FUSED','1':'CELL0','5':'ISO_RAW15','6':'COMMON_SOURCE','3':'ISO_NEG5','4':'ISO_NEG5'},status='CONDITIONAL')
s.part('FCC3','Fuse','600mA anti-surge input','UNRESOLVED',{'1':'HOST_5V','2':'HOST_5V_FUSED'},status='OPEN')
s.c('CCC1','10u 50V','HOST_5V_FUSED','CELL0');s.c('CCC2','100n','ISO_RAW15','COMMON_SOURCE')
s.r('RCC8','2k','ISO_RAW15','COMMON_SOURCE','CRCW12062K00FKEA');s.r('RCC9','680','COMMON_SOURCE','ISO_NEG5','CRCW1206680RFKEA')
s.part('UCC2','TPS7A1601','TPS7A1601DGNR','TPS7A1601DGNR',{'8':'ISO_RAW15','5':'ISO_RAW15','1':'ISO_13V','2':'ISO_FB','4':'COMMON_SOURCE','9':'COMMON_SOURCE'},'Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm')
s.r('RCC10','100k','ISO_13V','ISO_FB');s.r('RCC11','10k','ISO_FB','COMMON_SOURCE')
s.c('CCC3','10u 50V','ISO_RAW15','COMMON_SOURCE');s.c('CCC4','10u 50V','ISO_13V','COMMON_SOURCE')
s.part('DCC4','Diode','LDO reverse discharge','SS14',{'1':'ISO_RAW15','2':'ISO_13V'},'Diode_SMD:D_SMA')
s.part('UCC3','ADUM4120','ADuM4120CRIZ','ADuM4120CRIZ',{'1':'HOST_3V3','2':'DRIVE_ENABLE','3':'CELL0','4':'COMMON_SOURCE','5':'GATE_DRIVE','6':'ISO_13V'},'','DRAFT')
s.c('CCC5','100n','HOST_3V3','CELL0');s.c('CCC6','100n','ISO_13V','COMMON_SOURCE')
s.part('UCC4','TLV760','TLV76033DBZR','TLV76033DBZR',{'1':'ISO_3V3','2':'ISO_13V','3':'COMMON_SOURCE'},'Package_TO_SOT_SMD:SOT-23')
s.c('CCC7','100n','ISO_3V3','COMMON_SOURCE');s.r('RCC19','2k','ISO_3V3','COMMON_SOURCE')
s.part('UCC5','TPS3808','TPS3808G01DBVR','TPS3808G01DBVR',{'6':'ISO_3V3','5':'ISO_SENSE','3':'ISO_3V3','2':'COMMON_SOURCE','1':'ISO_RESET_N'},'Package_TO_SOT_SMD:SOT-23-6')
s.r('RCC12','287k','ISO_13V','ISO_SENSE');s.r('RCC13','10k','ISO_SENSE','COMMON_SOURCE');s.r('RCC14','10k','ISO_3V3','ISO_RESET_N')
s.r('RCC15','2k','ISO_RESET_N','ISO_BASE');s.r('RCC16','100k','ISO_BASE','COMMON_SOURCE')
s.part('QCC3','NPN','MMBT3904LT1G','MMBT3904LT1G',{'1':'ISO_BASE','2':'COMMON_SOURCE','3':'ISO_LED_K'},'Package_TO_SOT_SMD:SOT-23')
s.r('RCC17','2k','ISO_13V','ISO_LED_A','CRCW12062K00FKEA')
s.part('UCC6','Opto','VO617A-3X018T','VO617A-3X018T',{'1':'ISO_LED_A','2':'ISO_LED_K','4':'ISO_BAD','3':'CELL0'},'','CONDITIONAL')
s.r('RCC18','10k','HOST_3V3','ISO_BAD');s.inv('UCC7','ISO_BAD','ISO_OK');s.c('CCC8','100n','HOST_3V3','CELL0')
s.text(15,360,'13.123 V nominal regulator setting. Secondary supervisor nominal threshold 12.0285 V.\nMinimum output capacitor effective value >=2.2 uF. Verify startup/dropout and fast rail interruptions.\nMGJ1 3 kV functional working statement is NOT a certification of the whole board.',1.5)
s=sheet('permission','03 / Watchdog and deliberate permission','No supplied firmware heartbeat exists. GPIO4 reclamation requires a separate firmware change.\nALL_SAFE clears both latches asynchronously. Clearing a fault never sets PERMIT.')
s.part('UCC10','TPS3431','TPS3431SDRBR','TPS3431SDRBR',{'1':'HOST_3V3','2':'CWD','3':'SUP_OK','4':'CELL0','5':'HOST_3V3','6':'HEARTBEAT','7':'WD_OK','8':'WD_OK','9':'CELL0'},'Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm')
s.c('CCC10','1n C0G 1%','CWD','CELL0');s.r('RCC20','10k','HOST_3V3','WD_OK');s.r('RCC21','100k','HEARTBEAT','CELL0')
for ref,part,sense in [('UCC11','TPS3808G33DBVR','HOST_3V3'),('UCC12','TPS3808G50DBVR','HOST_5V')]:
 s.part(ref,'TPS3808',part,part,{'6':'HOST_3V3','5':sense,'3':'HOST_3V3','2':'CELL0','1':'SUP_OK'},'Package_TO_SOT_SMD:SOT-23-6')
s.r('RCC22','10k','HOST_3V3','SUP_OK');s.gate('UCC13','SUP_OK','WD_OK','SAFE1');s.gate('UCC14','POL_OK','SC_OK','SAFE2');s.gate('UCC15','SAFE1','SAFE2','SAFE3');s.gate('UCC16','ISO_OK','QUALIFIED_LINK','SAFE4');s.gate('UCC17','SAFE3','SAFE4','ALL_SAFE')
s.r('RCC23','100k','QUALIFIED_LINK','CELL0');s.r('RCC24','0','HOST_3V3','QUALIFIED_LINK',status='DNP')
s.inv('UCC18','HEARTBEAT','HEARTBEAT_EDGE')
s.part('UCC19','DFF','SN74LVC1G74DCUR','SN74LVC1G74DCUR',{'1':'HEARTBEAT_EDGE','2':'HOST_3V3','4':'CELL0','5':'HB_SEEN','6':'ALL_SAFE','7':'HOST_3V3','8':'HOST_3V3'},'Package_SO:VSSOP-8_2.3x2mm_P0.5mm')
s.inv('UCC20','CHG_REQ','REQ_LOW');s.gate('UCC21','HB_SEEN','REQ_LOW','ARM_DATA')
s.r('RCC25','10k','HOST_3V3','ARM_RAW');s.c('CCC11','100n','ARM_RAW','CELL0');s.part('SWCC1','Switch','Deliberate REARM','TL1105SPF160Q',{'1':'ARM_RAW','2':'CELL0'},status='DRAFT');s.inv('UCC22','ARM_RAW','ARM_EDGE')
s.part('UCC23','DFF','SN74LVC1G74DCUR','SN74LVC1G74DCUR',{'1':'ARM_EDGE','2':'ARM_DATA','4':'CELL0','5':'PERMIT','6':'ALL_SAFE','7':'HOST_3V3','8':'HOST_3V3'},'Package_SO:VSSOP-8_2.3x2mm_P0.5mm')
s.gate('UCC24','PERMIT','CHG_REQ','CMD1');s.gate('UCC25','CMD1','PSW_EN','CMD2');s.gate('UCC26','CMD2','ALL_SAFE','DRIVE_ENABLE')
s.r('RCC26','100k','CHG_REQ','CELL0');s.r('RCC27','100k','PSW_EN','CELL0');s.r('RCC28','10k','DRIVE_ENABLE','CELL0')
for i in range(10,27):s.c('CCC'+str(20+i),'100n','HOST_3V3','CELL0')
s.text(15,580,'Hardware arm button is a review interface, NOT a new fixed enclosure connector.\nRemove/replace with a deliberate software rearm interface only after GPIO ownership review.\nRCC24 is DNP: draft intentionally cannot enable charging before open qualification gates close.',1.5)
s=sheet('sensing','04 / Hardware polarity and fast current window','Independent analogue interlocks; no ADC or Lisp dependency. Ratios assume intact charge return.\nNew 10 mOhm Kelvin shunt is provisional; does not approve existing BQ calibration.')
for ref,a,b in [('RCC30','CHG_FUSED','POL_H1'),('RCC31','POL_H1','POL_H2'),('RCC32','POL_H2','POL_SENSE')]:s.r(ref,'330k',a,b)
s.r('RCC33','10k','HOST_3V3','POL_SENSE');s.r('RCC34','10k','POL_SENSE','CELL0');s.r('RCC35','10k','HOST_3V3','POL_REF');s.r('RCC36','10.2k','POL_REF','CELL0');s.c('CCC60','47p C0G','POL_SENSE','CELL0')
s.part('UCC30','CMP','TLV3201AIDBVR','TLV3201AIDBVR',{'3':'POL_SENSE','4':'POL_REF','1':'POL_OK','5':'HOST_3V3','2':'CELL0'},'Package_TO_SOT_SMD:SOT-23-5')
s.r('RCC37','10k','HOST_3V3','CURRENT_BIAS', 'RC0603BR-0710KL');s.r('RCC38','10k','RETURN_SENSE','CURRENT_BIAS','RC0603BR-0710KL');s.c('CCC61','47p C0G','CURRENT_BIAS','CELL0')
s.r('RCC39','10.7k','HOST_3V3','I_LOW','RC0603BR-0710K7L');s.r('RCC40','10k','I_LOW','CELL0','RC0603BR-0710KL');s.r('RCC41','10k','HOST_3V3','I_HIGH','RC0603BR-0710KL');s.r('RCC42','10.7k','I_HIGH','CELL0','RC0603BR-0710K7L')
for ref,plus,minus,out in [('UCC31','CURRENT_BIAS','I_LOW','SC_FORWARD_OK'),('UCC32','I_HIGH','CURRENT_BIAS','SC_REVERSE_OK')]:s.part(ref,'CMP','TLV3201AIDBVR','TLV3201AIDBVR',{'3':plus,'4':minus,'1':out,'5':'HOST_3V3','2':'CELL0'},'Package_TO_SOT_SMD:SOT-23-5')
s.gate('UCC33','SC_FORWARD_OK','SC_REVERSE_OK','SC_OK')
for i in range(4):s.c('CCC'+str(62+i),'100n','HOST_3V3','CELL0')
for ref,n in [('P5','HOST_3V3'),('P6','HOST_5V'),('P10','CELL0'),('P11','HOST_5V_FUSED')]:s.part(ref,'SupplyPort',n,'EXTERNAL_PREREQUISITE',{'1':n})
for ref,n in [('P7','HEARTBEAT'),('P8','CHG_REQ'),('P9','PSW_EN')]:s.part(ref,'Port',n,'INTERFACE',{'1':n})
s.text(15,360,'POL threshold nominal +4.90 V relative CELL0; reverse input remains within comparator common mode\nat +/-140 V with host alive. Host-off injection through divider needs an explicit clamp/disconnect review.\nCurrent window nominal +/-11.16 A at 3.3 V; tolerance sweep is in design note.\n47 pF filter: approximately 235 ns time constant. This is not a guaranteed whole-switch trip time.\nA bolted short needs bounded loop inductance and verified hot switching SOA, not just a comparator.',1.5)
# Fit tallest page to A1 rather than squeezing text.
for s in S:
 s.save()
 if s.name=='permission':
  path=P/(s.name+'.kicad_sch');path.write_text(path.read_text().replace('(paper "A2")','(paper "A1" portrait)'))
root=f'(kicad_sch (version 20250114) (generator "charge_control_draft") (uuid "{uid("root")}") (paper "A3") (lib_symbols)'
root+=f'(text "QFBMS charge-control review draft - NOT RELEASED\\nAGM option retained; voltage clamp / fuse coordination remain OPEN.\\nNo working PCB, supplied firmware, or existing schematic modified." (at 20 20 0) (effects (font (size 2 2)) (justify left top)) (uuid "{uid("roottext")}"))'
for i,s in enumerate(S):
 x=25+(i%2)*185;y=65+(i//2)*85
 root+=f'(sheet (at {x} {y}) (size 155 55) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid "{uid(s.name+"sheet")}") '+prop('Sheetname',s.title,x,y-3)+prop('Sheetfile',s.name+'.kicad_sch',x,y+58)+f'(instances (project "charge-control" (path "/{uid("root")}" (page "{i+2}")))))'
root+=')';(P/'charge-control.kicad_sch').write_text(root)
(P/'charge-control.kicad_pro').write_text('{}\n')
(P/'charge.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "charge_control_draft") '+''.join(v[0] for v in LIB.values())+')')
(P/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Charge") (type "KiCad") (uri "${KIPRJMOD}/charge.kicad_sym") (options "") (descr "Pin-explicit review symbols; manufacturer pin maps")))')
(P/'expected-connectivity.json').write_text(json.dumps(EXPECT,indent=2))
with (P/'bom.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(BOM[0]));w.writeheader();w.writerows(BOM)
print(len(BOM),'BOM rows; schematic draft written only under',P)
