#!/usr/bin/env python3
"""Local driver for the notjson challenge binary (x86-64 under qemu user)."""
import subprocess, sys, os, time, select

CHAL = "chal"
LD   = "/usr/x86_64-linux-gnu/lib64/ld-linux-x86-64.so.2"
SYSROOT = "/usr/x86_64-linux-gnu"

def start():
    return subprocess.Popen(
        ["qemu-x86_64-static", "-L", SYSROOT, LD, CHAL],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def read_until(p, token, timeout=10):
    """Read until token (bytes) appears in accumulated output."""
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([p.stdout], [], [], 0.5)
        if r:
            chunk = os.read(p.stdout.fileno(), 65536)
            if not chunk:
                break
            buf += chunk
            if token and token in buf:
                break
        elif p.poll() is not None:
            break
    return buf

def run(payload, token=b"Enter your JSON:", timeout=10):
    p = start()
    try:
        out = read_until(p, token, timeout)
        p.stdin.write(payload)
        p.stdin.flush()
        rest = read_until(p, None, timeout)
        return out + rest
    finally:
        try:
            p.kill()
        except Exception:
            pass
        p.wait()

if __name__ == "__main__":
    data = sys.stdin.buffer.read()
    sys.stdout.buffer.write(run(data))
