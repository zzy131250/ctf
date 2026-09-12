import numpy as np
from PIL import Image, ImageDraw
b=np.load('blocks2.npy')
y0,y1,x0,x1=200,650,150,3500
ink=(b[y0:y1,x0:x1]==122).astype(np.uint8)*255
im=Image.fromarray(ink,'L')
w,h=im.size
px=im.load()
comps=[]
val=128
for yy in range(h):
    for xx in range(w):
        if px[xx,yy]==255:
            ImageDraw.floodfill(im,(xx,yy),val,thresh=0)
            # bbox of val
            arr=np.array(im)
            ys,xs=np.where(arr==val)
            comps.append((len(xs),xs.min()+x0,xs.max()+x0,ys.min()+y0,ys.max()+y0))
            val+=1
            if val>255: val=1
print('components',len(comps))
comps.sort(reverse=True)
for c in comps[:40]:
    print('area',c[0],'x',c[1],c[2],'y',c[3],c[4])
