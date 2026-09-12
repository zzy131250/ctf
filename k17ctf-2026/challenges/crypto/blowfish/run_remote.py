import sys, time
from oracle import RemoteOracle
from attack import Attacker, TARGET, TINT

o = RemoteOracle()
t0 = time.time()
at = Attacker(o)
t = at.forge()
if t is None:
    print("[*] target not in span of initial fish blocks; pulling encrypted blocks", flush=True)
    at.add_enc_blocks(150)
    t = at.forge()
assert t is not None, "forgery failed"
assert t[2] == TARGET, "forged block mismatch"
print("[*] forged", t[2].hex(), "queries so far", at.nq, "%.1fs" % (time.time()-t0), flush=True)

# message = IV-block || '{"admin"' || ': true} '  -> bytes[8:] == '{"admin": true} '
M = at.chunks[0] + at.chunks[1] + t[2]
sig = at.digs[0] + at.digs[1] + t[1]
print("[*] submitting admin message", flush=True)
flag, resp = o.submit_admin(M.hex(), sig)
print("[*] response tail:", resp[-300:])
if flag:
    print("FLAG:", flag)
else:
    print("no flag found")
