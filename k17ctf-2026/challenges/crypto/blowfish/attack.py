import sys

TARGET = b': true} '   # second chunk of {"admin": true}
TINT = int.from_bytes(TARGET, 'big')


def popcount(x):
    return bin(x).count('1')


class Attacker:
    def __init__(self, oracle, verbose=True):
        self.o = oracle
        self.verbose = verbose
        fish, sig = oracle.initial()
        self.fish = fish
        n = len(fish) // 8
        self.chunks = [fish[i*8:(i+1)*8] for i in range(n)]
        self.digs = [sig[i*64:(i+1)*64] for i in range(n)]
        self.atoms = [(int.from_bytes(c, 'big'), d, c)
                      for c, d in zip(self.chunks, self.digs)]
        self.nq = 0
        self.base = 1   # the `{"admin"` chunk, used as an extra signed block
        if self.verbose:
            print(f"[*] fish len {len(fish)} full chunks {n} tail {fish[n*8:]}", flush=True)

    # ---------- oracle primitives ----------
    def xor3(self, a, b, c):
        """return atom equal to a^b^c, costs 2 oracle queries"""
        r = self.o.blow(a[2].hex() + b[2].hex(), a[1] + b[1])
        self.nq += 1
        assert r, "blow rejected"
        f1 = bytes.fromhex(r[0])
        if len(f1) != 16:
            raise RuntimeError("unexpected blow output len %d" % len(f1))
        e = (int.from_bytes(f1[8:16], 'big'), r[1][64:128], f1[8:16])
        d = self.atoms[self.base]
        r2 = self.o.unblow(c[2].hex() + e[2].hex() + d[2].hex(), c[1] + e[1] + d[1])
        self.nq += 1
        assert r2, "unblow rejected"
        f2 = bytes.fromhex(r2[0])
        if len(f2) < 16:
            raise RuntimeError("decrypt data vanished")
        t = (int.from_bytes(f2[8:16], 'big'), r2[1][64:128], f2[8:16])
        if t[0] != a[0] ^ b[0] ^ c[0]:
            raise RuntimeError("xor3 mismatch")
        return t

    def build_xor(self, mask):
        """mask: bitmask over atoms; returns atom = XOR of those blocks"""
        idx = [i for i in range(mask.bit_length()) if (mask >> i) & 1]
        assert len(idx) % 2 == 1, "need odd leaf count"
        return self._build(idx)

    def _build(self, idx):
        if len(idx) == 1:
            return self.atoms[idx[0]]
        a = self._build(idx[0:1])
        b = self._build(idx[1:2])
        c = self._build(idx[2:])
        return self.xor3(a, b, c)

    # ---------- GF(2)^64 linear algebra with bitmask expressions ----------
    def make_basis(self):
        basis = {}
        zero_masks = []
        for i, at in enumerate(self.atoms):
            val = at[0]
            mask = 1 << i
            added = False
            for bit in range(63, -1, -1):
                if not (val >> bit) & 1:
                    continue
                if bit not in basis:
                    basis[bit] = (val, mask)
                    added = True
                    break
                v2, m2 = basis[bit]
                val ^= v2
                mask ^= m2
            if not added and mask:
                zero_masks.append(mask)
        self.basis = basis
        self.zero_masks = zero_masks
        if self.verbose:
            print(f"[*] basis rank {len(basis)}, {len(zero_masks)} zero relations", flush=True)
        return basis

    def solve(self, target):
        val = target
        mask = 0
        for bit in range(63, -1, -1):
            if not (val >> bit) & 1:
                continue
            if bit not in self.basis:
                return None
            v2, m2 = self.basis[bit]
            val ^= v2
            mask ^= m2
        return mask if val == 0 else None

    def reduce_mask(self, mask):
        """replace triples a^b^c=0 inside the mask by nothing (keeps XOR value)"""
        changed = True
        while changed and popcount(mask) > 1:
            changed = False
            present = {}
            idx = [i for i in range(mask.bit_length()) if (mask >> i) & 1]
            for i in idx:
                present[self.atoms[i][0]] = i
            for i in idx:
                for j in idx:
                    if j <= i:
                        continue
                    v = self.atoms[i][0] ^ self.atoms[j][0]
                    if v in present:
                        k = present[v]
                        if k != i and k != j:
                            mask ^= (1 << i) | (1 << j) | (1 << k)
                            changed = True
                            break
                if changed:
                    break
        return mask

    def add_enc_blocks(self, count=150):
        """one chained blow query -> many fresh signed blocks (E images)"""
        use = self.chunks[:count]
        digs = self.digs[:count]
        r = self.o.blow(b''.join(use).hex(), ''.join(digs))
        self.nq += 1
        assert r, "chain blow rejected"
        out = bytes.fromhex(r[0])
        sig2 = r[1]
        nb = len(out) // 8
        new = 0
        for i in range(1, nb):
            blk = out[i*8:(i+1)*8]
            self.atoms.append((int.from_bytes(blk, 'big'), sig2[i*64:(i+1)*64], blk))
            new += 1
        if self.verbose:
            print(f"[*] chained blow added {new} signed blocks (total atoms {len(self.atoms)})", flush=True)
        return new

    def forge(self, target=TINT):
        self.make_basis()
        mask = self.solve(target)
        if mask is None:
            return None
        mask = self.reduce_mask(mask)
        if popcount(mask) % 2 == 0:
            for zm in self.zero_masks:
                if popcount(zm) % 2 == 1:
                    mask ^= zm
                    break
            else:
                raise RuntimeError("no odd zero-relation for parity fix")
            mask = self.reduce_mask(mask)
            if popcount(mask) % 2 == 0:
                for zm in self.zero_masks:
                    if popcount(zm) % 2 == 1:
                        mask ^= zm
                        break
        if popcount(mask) == 1:
            return self.atoms[[i for i in range(mask.bit_length()) if (mask >> i) & 1][0]]
        if self.verbose:
            print(f"[*] solution uses {popcount(mask)} leaves -> "
                  f"{(popcount(mask)-1)//2} xor3 ops", flush=True)
        return self.build_xor(mask)


if __name__ == '__main__':
    from oracle import LocalOracle
    o = LocalOracle()
    at = Attacker(o)
    t = at.forge()
    if t is None:
        print("[*] target not in span of initial chunks; adding encrypted blocks")
        at.add_enc_blocks(150)
        t = at.forge()
    assert t is not None, "still not forgeable"
    print("[*] forged block:", t[2].hex(), "expected", TARGET.hex())
    assert t[2] == TARGET
    M = at.chunks[0] + at.chunks[1] + t[2]
    sig = at.digs[0] + at.digs[1] + t[1]
    print("[*] is_admin:", o.is_admin(M.hex()))
    assert o.is_admin(M.hex())
    print("[*] total oracle queries:", at.nq)
    print("[*] LOCAL TEST PASSED")
