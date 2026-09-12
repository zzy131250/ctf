#!/usr/bin/env python3
"""
shamir secret spilling.

P (deg < 16) is fully recoverable from the 16 leaked shares.  Q (deg < 32)
agrees with P on those same 16 points, so Q - P = R*Pi with Pi = prod(x - x_j)
and deg R < 16.  The challenge also guarantees

    |Q_i - P_i| < B   (i < 16)        and        |Q_i| < B   (i >= 16)

i.e. every coefficient of e := Q - P_pad is smaller than B = 2^273, while the
modulus is 2^512.  With a = Q's 24 known evaluations (16 old + 8 new),

    A e = b   (mod MOD)

is a 24x32 system, so e lies in a coset of a rank-32 lattice of determinant
MOD^24.  A random coset representative is ~MOD^(24/32) = 2^384 away from the
origin; the true e sits at 2^276.  That gap is what makes it findable: LLL on
a Kannan embedding picks it straight out.
"""
import ast
import re
import sys
from pathlib import Path

from fpylll import IntegerMatrix, LLL

HERE = Path(__file__).resolve().parent
SRC = Path("out.txt")

N_LOW = 16        # deg P < 16
N_ALL = 32        # deg Q < 32
N_FREE = N_ALL - (N_LOW + 8)   # 8 leftover degrees of freedom


def load():
    src = SRC.read_text()
    g = lambda n: ast.literal_eval(re.search(rf"^{n} = (.*)$", src, re.M).group(1).strip())
    return g("MOD"), g("B"), g("known"), g("new")


def interpolate(pts, q):
    """Lagrange-interpolate; returns coefficients, low to high."""
    n = len(pts)
    xs = [x for x, _ in pts]
    out = [0] * n
    for i in range(n):
        num = [1]
        den = 1
        for j in range(n):
            if i == j:
                continue
            num = [0] + num                       # multiply by x
            for k in range(len(num) - 1):
                num[k] = (num[k] - xs[j] * num[k + 1]) % q
            den = den * (xs[i] - xs[j]) % q
        inv = pow(den, -1, q)
        yi = pts[i][1]
        for k in range(n):
            out[k] = (out[k] + yi * num[k] * inv) % q
    return out


def poly_eval(coeffs, x, q):
    r = 0
    for c in reversed(coeffs):
        r = (r * x + c) % q
    return r


def rref_aug(A, q):
    """RREF of the augmented matrix [A | rhs] mod q. -> (M, pivots, free)"""
    M = [row[:] for row in A]
    rows, cols = len(M), len(M[0]) - 1        # last col is rhs
    pivots, r = [], 0
    for c in range(cols):
        p = next((i for i in range(r, rows) if M[i][c] % q), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        inv = pow(M[r][c], -1, q)
        M[r] = [(x * inv) % q for x in M[r]]
        for i in range(rows):
            if i != r and M[i][c] % q:
                f = M[i][c]
                M[i] = [(M[i][j] - f * M[r][j]) % q for j in range(cols + 1)]
        pivots.append(c)
        r += 1
        if r == rows:
            break
    # inconsistent?
    for i in range(r, rows):
        if all(M[i][j] % q == 0 for j in range(cols)) and M[i][cols] % q:
            raise SystemExit("[!] system inconsistent - wrong model")
    free = [c for c in range(cols) if c not in pivots]
    return M, pivots, free


def main():
    q, B, known, new = load()
    print(f"[*] MOD bits={q.bit_length()}  B bits={B.bit_length()}")

    # ---- 1. recover P from the 16 leaked shares -------------------------
    P = interpolate(known, q)
    assert all(poly_eval(P, x, q) == y for x, y in known), "P interpolation failed"
    print("[*] P recovered (deg < 16), verified on all 16 leaked shares")

    # ---- 2. build the linear system on e = Q - P_pad --------------------
    T = P + [0] * (N_ALL - N_LOW)             # P padded with zeros
    pts = known + new                          # 24 evaluations of Q
    A, y = [], []
    for x, val in pts:
        A.append([pow(x, j, q) for j in range(N_ALL)])
        y.append(val)
    # b = y - A*T  (mod q)
    b = [(y[i] - sum(A[i][j] * T[j] for j in range(N_ALL))) % q for i in range(len(pts))]

    aug = [A[i] + [b[i]] for i in range(len(pts))]
    M, pivots, free = rref_aug(aug, q)
    print(f"[*] {len(pivots)} pivotal columns, {len(free)} free columns")

    # particular solution e0 (free vars = 0)
    e0 = [0] * N_ALL
    for i, c in enumerate(pivots):
        e0[c] = M[i][N_ALL] % q

    # ---- 3. lattice basis of ker(A mod q) -------------------------------
    #   q*e_p for pivot columns, plus one nullspace vector per free column
    L = []
    for c in pivots:
        row = [0] * N_ALL
        row[c] = q
        L.append(row)
    for f in free:
        u = [0] * N_ALL
        u[f] = 1
        for i, c in enumerate(pivots):
            u[c] = (-M[i][f]) % q
        L.append(u)
    assert len(L) == N_ALL

    # ---- 4. Kannan embedding: find v in L closest to -e0 -----------------
    target = [(-x) % q for x in e0]
    Msc = B
    dim = N_ALL + 1
    rows = [L[i] + [0] for i in range(N_ALL)] + [target + [Msc]]

    Bm = IntegerMatrix.from_matrix(rows)
    for prec in (1024, 2048, 4096):
        Bm2 = IntegerMatrix.from_matrix(rows)
        LLL.reduction(Bm2, delta=0.99, method="proved", float_type="mpfr", precision=prec)
        got = None
        for i in range(dim):
            row = [int(Bm2[i, j]) for j in range(dim)]
            if abs(row[-1]) == Msc:
                # last coord +-M  =>  first 32 coords are +-e
                cand = row[:N_ALL] if row[-1] == -Msc else [-v for v in row[:N_ALL]]
                cand = [(v % q) for v in cand]
                if all(abs(((v + q // 2) % q) - q // 2) < B for v in cand):
                    if all(sum(A[r][j] * cand[j] for j in range(N_ALL)) % q == b[r]
                           for r in range(len(pts))):
                        got = cand
                        break
        if got:
            print(f"[+] short vector found (mpfr precision={prec})")
            break
        print(f"[~] precision={prec}: no valid vector yet, retrying")
    else:
        raise SystemExit("[!] LLL did not surface the short vector")

    e = [((v + q // 2) % q) - q // 2 for v in got]    # centered
    print("[*] |e|_inf bits:", max(abs(v) for v in e).bit_length(), " (bound", B.bit_length(), ")")

    # ---- 5. rebuild Q and read the flag off Q(0) ------------------------
    Q = [(T[j] + e[j]) % q for j in range(N_ALL)]
    for x, val in pts:
        assert poly_eval(Q, x, q) == val, "Q does not match the known evaluations"
    print("[*] Q verified on all 24 shares")

    secret = Q[0] % q
    raw = secret.to_bytes((secret.bit_length() + 7) // 8, "big")
    print("\n[+] secret ->", raw)
    m = re.search(rb"K17\{[^}]*\}", raw)
    if m:
        print("[+] FLAG:", m.group(0).decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())
