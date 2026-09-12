import struct
d=open('AWholeNewWorld.wld','rb').read()
S=2753819
def i16(o): return struct.unpack_from('<h',d,o)[0]
def i32(o): return struct.unpack_from('<i',d,o)[0]
def pstr(o):
    n=0;sh=0
    while True:
        b=d[o]; o+=1
        n|=(b&0x7f)<<sh; sh+=7
        if not (b&0x80): break
    return d[o:o+n].decode('latin1'), o+n
o=S
cnt=i16(o); o+=2
chests=[]
for c in range(cnt):
    x=i32(o);y=i32(o+4);o+=8
    nm,o=pstr(o)
    n=i32(o); o+=4
    items=[]
    for i in range(n):
        q=i16(o); o+=2
        if q>0:
            t=i32(o); o+=4; p=d[o]; o+=1
            items.append((t,q,p))
    chests.append((x,y,nm,items))
print('chests',cnt,'end',o)
for idx,(x,y,nm,items) in enumerate(chests):
    if items or nm:
        print(idx,'(%d,%d)'%(x,y),'name=%r'%nm,'items=',items)
