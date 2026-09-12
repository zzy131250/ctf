import struct
d=open('AWholeNewWorld.wld','rb').read()
S=2753819; E=2772875
def u16(o): return struct.unpack_from('<H',d,o)[0]
def i16(o): return struct.unpack_from('<h',d,o)[0]
def i32(o): return struct.unpack_from('<i',d,o)[0]
def pstr(o):
    n=0;sh=0
    while True:
        b=d[o]; o+=1
        n|=(b&0x7f)<<sh; sh+=7
        if not (b&0x80): break
    return d[o:o+n].decode('latin1'), o+n

# Variant B: count int2, per chest x,y,name, 40 items
def varB():
    o=S; cnt=i16(o); o+=2
    for c in range(cnt):
        x=i32(o);y=i32(o+4);o+=8
        nm,o=pstr(o)
        for i in range(40):
            q=i16(o); o+=2
            if q>0:
                t=i32(o); o+=4; pre=d[o]; o+=1
        if o>E: return ('overrun',c,o)
    return ('end',cnt,o)
print('B',varB())

# Variant C: count int2,max int2, per chest x,y,name, then until section end? no
# Variant D: int32 count
def varD():
    o=S; cnt=i32(o); o+=4
    print('  cnt32',cnt)
    return None
varD()

# Show first 80 bytes
print(' '.join('%02x'%b for b in d[S:S+80]))
print('first 40 as int16:', [i16(S+2*i) for i in range(20)])
