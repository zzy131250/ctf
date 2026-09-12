import struct
d=open('AWholeNewWorld.wld','rb').read()
S=2753819; E=2772875
def i16(o): return struct.unpack_from('<h',d,o)[0]
def i32(o): return struct.unpack_from('<i',d,o)[0]
def pstr(o):
    n=0;sh=0
    while True:
        b=d[o]; o+=1
        n|=(b&0x7f)<<sh; sh+=7
        if not (b&0x80): break
    return d[o:o+n].decode('latin1'), o+n

def run(hdr, nfield, itemfields):
    o=S
    cnt=i16(o); o+=2
    if hdr: o+=2
    try:
        for c in range(cnt):
            x=i32(o); y=i32(o+4); o+=8
            nm,o=pstr(o)
            n=i32(o) if nfield==4 else i16(o)
            o+=nfield
            for i in range(n):
                q=i16(o); o+=2
                if q>0:
                    if itemfields==5:
                        t=i32(o); o+=4; p=d[o]; o+=1
                    else:
                        t=i16(o); o+=2; p=d[o]; o+=1
            if o>E+10: return ('overrun',c,o)
        return ('end',cnt,o,o-E)
    except Exception as e:
        return ('err',e)

print('V hdr(max2)+n4+item5:', run(True,4,5))
print('V hdr(max2)+n2+item5:', run(True,2,5))
print('V nohdr+n4+item5   :', run(False,4,5))
print('V nohdr+n4+item3   :', run(False,4,3))
