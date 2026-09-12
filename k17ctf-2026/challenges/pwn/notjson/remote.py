#!/usr/bin/env python3
"""Remote driver for notjson (chal.secso.cc 4003)."""
import socket, time, re, sys

HOST, PORT = "chal.secso.cc", 4003

def conn(timeout=10):
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    s.settimeout(timeout)
    return s

def recv_until(s, token, timeout=10):
    buf = b""
    s.settimeout(timeout)
    end = time.time() + timeout
    while time.time() < end:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
        if token and token in buf:
            break
    return buf

def run(payload, token=b"Enter your JSON:", timeout=10, read_time=6.0):
    """Connect, send payload, read response."""
    s = conn(timeout)
    try:
        recv_until(s, token, timeout)
        s.sendall(payload)
        out = b""
        s.settimeout(read_time)
        end = time.time() + read_time
        while time.time() < end:
            try:
                chunk = s.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            out += chunk
            end = time.time() + 1.0   # keep a short tail timeout
        return out
    finally:
        try: s.close()
        except Exception: pass

if __name__ == "__main__":
    out = run(b'{"a|b":{}}')
    print(repr(out[-200:]))
