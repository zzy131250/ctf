#!/usr/bin/env python3
import subprocess,sys,re
CHAL='chal'
LD='/tmp/deb13/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2'
LIB='/tmp/deb13/usr/lib/x86_64-linux-gnu'
def run(idx,f1,f2='B',env=None):
    inp=(idx+'\n'+f1+'\n'+f2+'\n').encode('latin1')
    cmd=['qemu-x86_64-static',LD,'--library-path',LIB,CHAL]
    p=subprocess.run(cmd,input=inp,capture_output=True,timeout=25,env=env)
    return p.stdout.decode('latin1'),p.stderr.decode('latin1')
if __name__=='__main__':
    o,e=run(sys.argv[1] if len(sys.argv)>1 else '1', sys.argv[2] if len(sys.argv)>2 else '%p', sys.argv[3] if len(sys.argv)>3 else 'B')
    print('OUT:',repr(o)); print('ERR:',repr(e[:300]))
