import struct
d=open('AWholeNewWorld.wld','rb').read()
P=dict(header=167,tiles=11946,chests=2753819,signs=2772875,npcs=2772877,
       entities=2772945,plates=2772949,town=2772953,bestiary=2772957,
       journey=2772969,footer=2773000)
class R:
    def __init__(s,o): s.o=o
    def i1(s): v=d[s.o]; s.o+=1; return v
    def i2(s): v=struct.unpack_from('<h',d,s.o)[0]; s.o+=2; return v
    def u2(s): v=struct.unpack_from('<H',d,s.o)[0]; s.o+=2; return v
    def i4(s): v=struct.unpack_from('<i',d,s.o)[0]; s.o+=4; return v
    def u8(s): v=struct.unpack_from('<Q',d,s.o)[0]; s.o+=8; return v
    def f4(s): v=struct.unpack_from('<f',d,s.o)[0]; s.o+=4; return v
    def f8(s): v=struct.unpack_from('<d',d,s.o)[0]; s.o+=8; return v
    def s(sz=None):
        pass
    def string(s):
        n=0;sh=0
        while True:
            b=d[s.o]; s.o+=1
            n|=(b&0x7f)<<sh; sh+=7
            if not (b&0x80): break
        v=d[s.o:s.o+n].decode('latin1'); s.o+=n; return v
    def bits(s):
        b=s.i1(); return [(b>>i)&1 for i in range(8)]

# chests
r=R(P['chests'])
cnt=r.i2(); mx=r.i2()
print('chests count',cnt,'maxitems',mx)
chests=[]
for c in range(cnt):
    x=r.i4(); y=r.i4(); nm=r.string(); items=[]
    for i in range(mx):
        q=r.i2()
        if q>0:
            t=r.i4(); pre=r.i1(); items.append((t,q,pre))
    chests.append((x,y,nm,items))
print('chests end',r.o,'expected',P['signs'],'OK' if r.o==P['signs'] else 'MISMATCH')
import collections
allitems=[it for c in chests for it in c[3]]
print('total items',len(allitems))
print('sample chests:',chests[:3])
print('named chests:',[ (c[0],c[1],c[2]) for c in chests if c[2]])
