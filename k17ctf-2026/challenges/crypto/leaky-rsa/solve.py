#!/usr/bin/env python3
# leaky rsa: e=257, leak = dp + dq where dp = d mod (P-1), dq = d mod (Q-1)
import re, math
from Crypto.Util.number import long_to_bytes

txt = open("out.txt").read()
N = int(re.search(r"N = (\d+)", txt).group(1))
e = int(re.search(r"e = (\d+)", txt).group(1))
leak = int(re.search(r"leak = (\d+)", txt).group(1))
c = int(re.search(r"c = (\d+)", txt).group(1))

# e*dp = 1 + kp*(P-1), 1 <= kp <= e-1 ; same for dq
# e*leak - 2 = kp*(P-1) + kq*(Q-1)  =>  kp*P + kq*Q = e*leak - 2 + kp + kq =: C
# with PQ=N: -kp*P^2 + C*P - kq*N = 0  => disc = C^2 - 4*kp*kq*N must be a perfect square

found = None
base = e * leak - 2
for kp in range(1, e):
    for kq in range(1, e):
        C = base + kp + kq
        D = C * C - 4 * kp * kq * N
        if D < 0:
            continue
        s = math.isqrt(D)
        if s * s == D:
            num = C + s
            if num % (2 * kp):
                continue
            P = num // (2 * kp)
            if P > 1 and N % P == 0:
                Q = N // P
                # sanity: P != Q, bits
                if P != Q:
                    found = (P, Q, kp, kq)
                    break
    if found:
        break

assert found, "no factor found"
P, Q, kp, kq = found
print(f"[+] kp={kp} kq={kq}")
print(f"[+] P bits={P.bit_length()} Q bits={Q.bit_length()}")
# verify dp/dq consistency
phi = (P - 1) * (Q - 1)
d = pow(e, -1, phi)
dp, dq = d % (P - 1), d % (Q - 1)
assert dp + dq == leak, "leak mismatch"
print("[+] leak verified (dp+dq == leak)")
m = pow(c, d, N)
flag = long_to_bytes(m)
print("[+] flag ->", flag)
print(flag.decode())
