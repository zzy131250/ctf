#!/usr/bin/env python3
"""Local probe: feed chal a format string, capture output."""
import subprocess, sys, os

CHAL = sys.argv[1] if len(sys.argv) > 1 else './hard/huge-binary-2/chal'
IDX  = sys.argv[2] if len(sys.argv) > 2 else '1'
FMT1 = sys.argv[3] if len(sys.argv) > 3 else '%p'
FMT2 = sys.argv[4] if len(sys.argv) > 4 else 'B'

inp = (IDX + '\n' + FMT1 + '\n' + FMT2 + '\n').encode()
p = subprocess.run(['qemu-x86_64-static', '-L', '/usr/x86_64-linux-gnu', CHAL],
                   input=inp, capture_output=True, timeout=20)
print("STDOUT:", p.stdout.decode('latin1'))
print("STDERR:", p.stderr.decode('latin1')[:500])
print("RC:", p.returncode)
