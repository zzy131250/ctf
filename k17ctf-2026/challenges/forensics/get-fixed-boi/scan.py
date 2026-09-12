import struct
d=open('AWholeNewWorld.wld','rb').read()
def pstring(o):
    n=0;sh=0
    while True:
        b=d[o]; o+=1
        n|=(b&0x7f)<<sh; sh+=7
        if not (b&0x80): break
    return d[o:o+n].decode('latin1'), o+n
def try_chests(o):
    try:
        cnt=struct.unpack_from('<h',d,o)[0]; mx=struct.unpack_from('<h',d,o+2)[0]
        if not (0<=cnt<=200 and 1<=mx<=200): return None
        p=o+4
        for c in range(cnt):
            x,y=struct.unpack_from('<2i',d,p); p+=8
            nm,p=pstring(p)
            for i in range(mx):
                q=struct.unpack_from('<h',d,p)[0]; p+=2
                if q>0:
                    t=struct.unpack_from('<i',d,p)[0]; p+=4
                    pre=d[p]; p+=1
        return p
    except Exception:
        return None
signs=2772875
for o in range(2753819,2772876):
    e=try_chests(o)
    if e==signs:
        cnt=struct.unpack_from('<h',d,o)[0]; mx=struct.unpack_from('<h',d,o+2)[0]
        print('FOUND chests at',o,'cnt',cnt,'max',mx,'ends',e)
