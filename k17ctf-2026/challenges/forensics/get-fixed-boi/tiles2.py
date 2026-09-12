import struct, numpy as np
d=open('AWholeNewWorld.wld','rb').read()
W,H=4200,1200
mask=d[72:72+95]; tfimp=[]
for byte in mask:
    for i in range(8): tfimp.append((byte>>i)&1)
tfimp=tfimp[:753]
o=11946
blocks=np.full((H,W),-1,dtype=np.int16)
walls=np.full((H,W),-1,dtype=np.int16)
for x in range(W):
    y=0
    while y<H:
        f1=d[o]; o+=1
        if f1&1: f2=d[o]; o+=1
        else: f2=0
        if f2&1: f3=d[o]; o+=1
        else: f3=0
        if f3&1: f4=d[o]; o+=1
        else: f4=0
        hb=(f1>>1)&1; hxb=(f1>>5)&1; isbp=(f3>>3)&1
        hw=(f1>>2)&1; hxw=(f3>>6)&1; iswp=(f3>>4)&1
        liquid=(f1>>3)&3; rle=(f1>>6)&3
        btype=-1
        if hb:
            btype=struct.unpack_from('<H',d,o)[0] if hxb else d[o]
            o+= 2 if hxb else 1
            if btype<len(tfimp) and tfimp[btype]: o+=4
            if isbp: o+=1
        wtype=-1
        if hw:
            wl=d[o]; o+=1
            if iswp: o+=1
            wtype=wl
        if liquid: o+=1
        if hxw:
            wg=d[o]; o+=1
            wtype = wtype + wg*256 if wtype>=0 else wg*256
        if rle==2: mult=struct.unpack_from('<H',d,o)[0]+1; o+=2
        elif rle==1: mult=d[o]+1; o+=1
        else: mult=1
        me=min(y+mult,H)
        if btype>=0: blocks[y:me,x]=btype
        if wtype>=0: walls[y:me,x]=wtype
        y=me
assert o==2753819, o
np.save('blocks2.npy',blocks); np.save('walls2.npy',walls)
print('ok saved', o)
# palette
from PIL import Image
pal={-1:(135,206,235)}  # sky
# common
colors={0:(150,111,74),1:(128,128,128),57:(80,160,60),122:(90,70,140),59:(110,90,160),
        53:(60,100,200),44:(200,200,90),161:(120,120,120),60:(150,130,90),25:(200,50,50),
        51:(50,180,180),147:(180,120,60),396:(140,100,80),58:(90,60,40),226:(100,160,220),
        123:(150,80,150),368:(70,70,90),165:(60,170,90),367:(120,60,90),397:(120,120,90),
        62:(60,40,30),28:(130,100,80),184:(200,180,110),633:(60,60,70),7:(120,90,60),
        183:(120,90,70),167:(200,150,90),168:(190,150,110),189:(110,110,150),75:(80,220,120)}
def render(arr, fn, scale=2):
    im=np.zeros((H,W,3),dtype=np.uint8)
    u=np.unique(arr)
    for v in u:
        c=colors.get(int(v))
        if c is None:
            # pseudo color
            vv=int(v)&0xffff
            c=((vv*37)%200+30,(vv*91)%200+30,(vv*53)%200+30)
        im[arr==v]=c
    img=Image.fromarray(im).resize((W//scale,H//scale), Image.NEAREST)
    img.save(fn)
    print('saved',fn)
render(blocks,'world_blocks.png',2)
render(walls,'world_walls.png',2)
