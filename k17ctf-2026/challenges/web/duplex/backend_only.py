#!/usr/bin/env python3
"""Fake backend: listens on 127.0.0.1:80 (needs root), dumps what it receives."""
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 80
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/duplex_backend.log"

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", PORT))
srv.listen(5)
srv.settimeout(60)
with open(OUT, "ab", buffering=0) as log:
    log.write(b"<<LISTENING>>\n")
    try:
        while True:
            c, _ = srv.accept()
            c.settimeout(2)
            buf = b""
            try:
                while True:
                    b = c.recv(65536)
                    if not b:
                        break
                    buf += b
            except socket.timeout:
                pass
            log.write(b"<<REQ %d bytes>>\n" % len(buf) + buf + b"\n<<END>>\n")
            c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nFAKE\n")
            c.close()
    except Exception:
        pass
