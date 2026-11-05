from pathlib import Path
p=Path('design/charge-control/build_draft.py');s=p.read_text();s=s.replace('else:x,y=xy\n  s=', 'else:x,y=xy\n  x=round(round(x/1.27)*1.27,2);y=round(round(y/1.27)*1.27,2)\n  s=')
s=s.replace('HVSSOP-8-1EP_3x3mm_P0.65mm\'','HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm\'').replace('VSON-8-1EP_3x3mm_P0.65mm_EP1.5x2.4mm','VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm')
s=s.replace("s.r('RCC15','10k'", "s.r('RCC15','2k'")
s=s.replace("s.c('CCC7','100n','ISO_3V3','COMMON_SOURCE')", "s.c('CCC7','100n','ISO_3V3','COMMON_SOURCE');s.r('RCC19','2k','ISO_3V3','COMMON_SOURCE')")
s=s.replace("[('P5','HOST_3V3'),('P6','HOST_5V')]", "[('P5','HOST_3V3'),('P6','HOST_5V'),('P10','CELL0'),('P11','HOST_5V_FUSED')]")
s=s.replace("'Resistor_SMD:R_0603_1608Metric',status)", "('Resistor_SMD:R_1206_3216Metric' if mpn and mpn.startswith('CRCW1206') else 'Resistor_SMD:R_0603_1608Metric'),status)")
p.write_text(s)
