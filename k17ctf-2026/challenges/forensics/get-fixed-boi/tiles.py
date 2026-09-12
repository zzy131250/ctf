import struct, sys, time
d=open('AWholeNewWorld.wld','rb').read()
W,H=4200,1200
# tileframeimportant mask
mask=d[72:72+95]
tfimp=[]
for byte in mask:
    for i in range(8):
        tfimp.append((byte>>i)&1)
tfimp=tfimp[:753]
o=11946
import numpy as np
blocks=np.zeros((H,W),dtype=np.int16)  # 0=none
walls=np.zeros((H,W),dtype=np.int16)
t0=time.time()
count=0
for x in range(W):
    y=0
    while y<H:
        f1=d[o]; o+=1
        hf2=f1&1
        if hf2: f2=d[o]; o+=1
        else: f2=0
        hf3=f2&1
        if hf3: f3=d[o]; o+=1
        else: f3=0
        hf4=f3&1
        if hf4: f4=d[o]; o+=1
        else: f4=0
        has_block=(f1>>1)&1
        has_ext_block=(f1>>5)&1
        is_block_painted=(f3>>3)&1
        has_wall=(f1>>2)&1
        has_ext_wall=(f3>>6)&1
        is_wall_painted=(f3>>4)&1
        liquid=(f1>>3)&3
        rle=(f1>>6)&3
        btype=0
        if has_block:
            if has_ext_block:
                btype=struct.unpack_from('<H',d,o)[0]; o+=2
            else:
                btype=d[o]; o+=1
            if btype<len(tfimp) and tfimp[btype]:
                o+=4  # frame u16,u16
            if is_block_painted: o+=1
        if has_wall:
            o+=1
            if is_wall_painted: o+=1
        if liquid: o+=1
        if has_ext_wall: o+=1
        if rle==2:
            mult=struct.unpack_from('<H',d,o)[0]+1; o+=2
        elif rle==1:
            mult=d[o]+1; o+=1
        else:
            mult=1
        me=min(y+mult,H)
        if has_block:
            blocks[y:me,x]=btype
        if has_wall:
            pass
        y=me
        count+=1
        if o>len(d): print('overrun at col',x); sys.exit()
print('end offset',o,'target',2753819,'diff',o-2753819,'time',time.time()-t0,'blocksread',count)
np.save('blocks.npy',blocks)
