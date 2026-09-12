#!/usr/bin/env python3
"""Full-affine registration from stroke-mask moments + local shift search.

Question: after aligning two photos of the same cat drawing, do the high-pass
noise fields correlate (fixed sensor pattern) or not (independent noise)?
"""
import sys

import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float32)


def blur(a, k=5):
    P = np.pad(a, k // 2, mode="edge")
    out = np.zeros_like(a)
    for dy in range(k):
        for dx in range(k):
            out += P[dy : dy + a.shape[0], dx : dx + a.shape[1]]
    return out / (k * k)


def residual(a):
    r = a - blur(a, 5)
    return r - r.mean()


def stroke_mask(a):
    return a < (np.median(a) - 12)


def affine_from_moments(src_mask, dst_mask):
    """2x3 affine A with A @ src_pts ~ dst_pts, from second moments."""
    def mom(m):
        ys, xs = np.nonzero(m)
        c = np.array([xs.mean(), ys.mean()])
        d = np.stack([xs - c[0], ys - c[1]])
        cov = (d @ d.T) / len(xs)
        return c, cov

    c1, C1 = mom(src_mask)
    c2, C2 = mom(dst_mask)
    # whitening of src, colouring of dst
    w1, v1 = np.linalg.eigh(C1)
    w2, v2 = np.linalg.eigh(C2)
    W1 = v1 @ np.diag(1 / np.sqrt(np.maximum(w1, 1e-9))) @ v1.T
    W2 = v2 @ np.diag(np.sqrt(np.maximum(w2, 1e-9))) @ v2.T
    M = W2 @ W1
    A = np.zeros((2, 3))
    A[:, :2] = M
    A[:, 2] = c2 - M @ c1
    return A


def warp(a, A, shape):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    Ai = np.linalg.inv(np.vstack([A, [0, 0, 1]]))[:2]
    sx = Ai[0, 0] * xx + Ai[0, 1] * yy + Ai[0, 2]
    sy = Ai[1, 0] * xx + Ai[1, 1] * yy + Ai[1, 2]
    ok = (sx >= 1) & (sy >= 1) & (sx < a.shape[1] - 2) & (sy < a.shape[0] - 2)
    x0 = np.clip(np.floor(sx).astype(np.int32), 0, a.shape[1] - 2)
    y0 = np.clip(np.floor(sy).astype(np.int32), 0, a.shape[0] - 2)
    fx = np.clip(sx - x0, 0, 1)
    fy = np.clip(sy - y0, 0, 1)
    v = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
         + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)
    return v, ok


def ncc(x, y, ok):
    a = x[ok]
    b = y[ok]
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).mean() / (a.std() * b.std() + 1e-12))


def best_shift_ncc(ra, rb, ok, span=4):
    """Shift rb by (dy,dx) and return the best NCC found."""
    best = (-9, 0, 0)
    for dy in range(-span, span + 1):
        for dx in range(-span, span + 1):
            rs = np.roll(np.roll(rb, dy, 0), dx, 1)
            v = ncc(ra, rs, ok)
            if v > best[0]:
                best = (v, dy, dx)
    return best


def main():
    ref = load(sys.argv[1])
    mref = stroke_mask(ref)
    rref = residual(ref)
    for other in sys.argv[2:]:
        o = load(other)
        A = affine_from_moments(stroke_mask(o), mref)
        ow, ok = warp(o, A, ref.shape)
        rw, _ = warp(residual(o), A, ref.shape)
        ok &= np.abs(ow - ow.mean()) < 60  # drop pixels that landed outside the scene
        v, dy, dx = best_shift_ncc(rref, rw, ok)
        print(f"{sys.argv[1].split('/')[-1]} <- {other.split('/')[-1]}  "
              f"overlap={ok.mean():.3f}  bestNCC={v:+.4f} @ ({dy},{dx})")


if __name__ == "__main__":
    main()
