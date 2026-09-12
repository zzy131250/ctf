import sys,re
from rprobe import run
# f2 = 'B' so buf2[0]=0x42 ; f1='%p' short so buf1[0]='%'=0x25
for idx in [-81,-80,-79,-78,-49,-48,-47,-46,-9,-8,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,24,25,26]:
    try:
        lk,out=run(str(idx),'%p','B')
        print('idx=%-4d -> byte=%s'%(idx, hex(lk) if lk is not None else None))
    except Exception as e:
        print(idx,'ERR',e)
