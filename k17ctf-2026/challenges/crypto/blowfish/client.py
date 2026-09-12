import socket, sys, time

HOST, PORT = 'chal.secso.cc', 2001

class Conn:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=20)
        self.buf = b''
    def recv_until(self, marker, timeout=20):
        self.s.settimeout(timeout)
        while marker not in self.buf:
            d = self.s.recv(65536)
            if not d:
                break
            self.buf += d
        i = self.buf.find(marker)
        if i < 0:
            out, self.buf = self.buf, b''
            return out
        i += len(marker)
        out, self.buf = self.buf[:i], self.buf[i:]
        return out
    def recv_some(self, timeout=3, n=65536):
        self.s.settimeout(timeout)
        try:
            d = self.s.recv(n)
        except socket.timeout:
            return b''
        self.buf += d
        return d
    def send(self, data):
        if isinstance(data, str): data = data.encode()
        self.s.sendall(data)
    def close(self):
        try: self.s.close()
        except: pass

def grab():
    c = Conn()
    data = c.recv_until(b'? ')
    c.close()
    return data

if __name__ == '__main__':
    d = grab()
    print(d.decode(errors='replace'))
