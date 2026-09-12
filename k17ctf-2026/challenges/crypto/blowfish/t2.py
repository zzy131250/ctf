import resource, sys
from oracle import LocalOracle
print("importing attack", flush=True)
from attack import Attacker, TARGET, TINT
print("imported", flush=True)
o = LocalOracle()
at = Attacker(o)
print("attacker built", len(at.atoms), flush=True)
print("mem MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, flush=True)
a,b,c = at.atoms[0], at.atoms[1], at.atoms[2]
print("calling xor3", flush=True)
t = at.xor3(a,b,c)
print("xor3 ok", hex(t[0]) == hex(a[0]^b[0]^c[0]), flush=True)
print("mem MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, flush=True)
