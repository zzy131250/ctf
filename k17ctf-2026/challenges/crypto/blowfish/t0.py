import sys, resource
print("start", flush=True)
from oracle import LocalOracle
print("imported", flush=True)
o = LocalOracle()
print("oracle built", len(o.iv_fish), flush=True)
print("mem MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, flush=True)
f, s = o.initial()
print("initial ok", len(f), len(s), flush=True)
print("mem MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, flush=True)
