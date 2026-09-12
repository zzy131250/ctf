import sys, re
from rprobe import run
start,end=int(sys.argv[1]),int(sys.argv[2])
for n in range(start,end+1,5):
    grp=list(range(n,min(n+5,end+1)))
    fmt=''.join('%%%d$p.'%g for g in grp)[:-1]
    try:
        lk,out=run('1',fmt,'B')
        vals=[v for v in re.findall(r'0x[0-9a-f]+|\(nil\)',out)]
        print('%-16s -> %s'%(str(grp),vals))
    except Exception as e:
        print(grp,'ERR',e)
