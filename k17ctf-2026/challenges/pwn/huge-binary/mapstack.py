import re,sys
from rprobe import run
# arg6=argv, arg49=[rbp+0xe0]=PIE+0x10a1 (_start ret).  rbp = (argv & ~0xf) - 0x100
tests={
 'A':[6,20,27,38,50],
 'B':[6,35,46,49,21],
 'C':[6,22,25,28,39],
 'D':[6,40,42,45,19],
}
for tag,grp in tests.items():
    fmt=''.join('%%%d$p.'%g for g in grp)[:-1]
    for rep in range(2):
        try:
            lk,out=run('1',fmt,'B')
            v=re.findall(r'0x[0-9a-f]+|\(nil\)',out)
            argv=None
            try:
                argv=int(v[0],16)
                rbp=(argv & ~0xf)-0x100
            except: rbp=None
            disp=[]
            for x in v:
                if rbp is None: disp.append(x); continue
                if x=='(nil)': disp.append('nil'); continue
                y=int(x,16)
                d=y-rbp
                disp.append('%s (%+#x from rbp)'%(x,d) if abs(d)<0x4000 else x)
            print('%s argv=%s rbp=%s'%(tag,v[0],hex(rbp) if rbp else None))
            for g,x in zip(grp,disp): print('   arg%-3d %s'%(g,x))
        except Exception as e:
            print(tag,'ERR',e)
