import struct
d=open('AWholeNewWorld.wld','rb').read()
def i4(o): return struct.unpack_from('<i',d,o)[0]
def i2(o): return struct.unpack_from('<h',d,o)[0]
def f4(o): return struct.unpack_from('<f',d,o)[0]
def pstr(o):
    n=0;sh=0
    while True:
        b=d[o]; o+=1
        n|=(b&0x7f)<<sh; sh+=7
        if not (b&0x80): break
    return d[o:o+n].decode('latin1'), o+n
o=2772877
print('start',o)
print('int32@',i4(o)); o+=4
print('next bytes', ' '.join('%02x'%b for b in d[o:o+40]))
# print all bytes 2772895..2772945 with offset
for x in range(2772881,2772949):
    print(x, '%02x'%d[x], chr(d[x]) if 32<=d[x]<127 else '.')
