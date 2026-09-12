#!/usr/bin/env python3
"""Align two photos of the same scene via the shape moments of the dark strokes,
then see whether the high-pass noise agrees in the common frame.

If the per-camera PRNU was baked into the *scene* before the geometric
transform (rotate/scale), this is what it takes to expose it.
"""
import sys

import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float32)


def blur5(a):
    P = np.pad(a, 2, mode="edge")
    out = np.zeros_like(a)
    for dy in range(5):
        for dx in range(5):
            out += P[dy : dy + a.shape[0], dx : dx + a.shape[1]]
    return out / 25.0


def strokes(a):
    """Binary mask of the drawn lines (dark on light, plus the threshold band)."""
    return a < (np.median(a) - 12)


def moments(mask):
    ys, xs = np.nonzero(mask)
    w = np.ones_like(xs, dtype=np.float64)
    n = w.sum()
    cx, cy = (xs * w).sum() / n, (ys * w).sum() / n
    dx, dy = xs - cx, ys - cy
    cxx = (w * dx * dx).sum() / n
    cyy = (w * dy * dy).sum() / n
    cxy = (w * dx * dy).sum() / n
    return cx, cy, cxx, cyy, cxy


def frame(m):
    """Return (centre, angle, scale) of the moments: an oriented ellipse."""
    cx, cy, cxx, cyy, cxy = m
    cov = np.array([[cxx, cxy], [cxy, cyy]])
    val, vec = np.linalg.eigh(cov)
    order = np.argsort(val)[::-1]
    val, vec = val[order], vec[:, order]
    ang = np.arctan2(vec[1, 0], vec[0, 0])
    return np.array([cx, cy]), ang, np.sqrt(max(val[0], 1e-9))


def affine_map(src, dst):
    """Rotation/scale/translation taking src frame onto dst frame (2x3)."""
    (c1, a1, s1), (c2, a2, s2) = src, dst
    t = a2 - a1
    k = s2 / s1
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]]) * k
    A = np.zeros((2, 3), dtype=np.float64)
    A[:, :2] = R
    A[:, 2] = c2 - R @ c1
    return A


def warp(a, A, out_size):
    """Bilinear warp with A mapping dst coords -> src coords."""
    h, w = out_size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # inverse map
    Ai = np.linalg.inv(np.vstack([A, [0, 0, 1]]))[:2]
    sx = Ai[0, 0] * xx + Ai[0, 1] * yy + Ai[0, 2]
    sy = Ai[1, 0] * xx + Ai[1, 1] * yy + Ai[1, 2]
    x0 = np.floor(sx).astype(np.int32)
    y0 = np.floor(sy).astype(np.int32)
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < a.shape[1] - 1) & (y0 < a.shape[0] - 1)
    x0c = np.clip(x0, 0, a.shape[1] - 2)
    y0c = np.clip(y0, 0, a.shape[0] - 2)
    fx = sx - x0c
    fy = sy - y0c
    v = (
        a[y0c, x0c] * (1 - fx) * (1 - fy)
        + a[y0c, x0c + 1] * fx * (1 - fy)
        + a[y0c + 1, x0c] * (1 - fx) * fy
        + a[y0c + 1, x0c + 1] * fx * fy
    )
    return v, ok


def residual(a):
    r = a - blur5(a)
    return r - r.mean()


def ncc_in(a, b, ok):
    x = a[ok]
    y = b[ok]
    x = x - x.mean()
    y = y - y.mean()
    return float((x * y).mean() / (x.std() * y.std() + 1e-12))


def main():
    ref = sys.argv[1]
    for other in sys.argv[2:]:
        a, b = load(ref), load(other)
        fa = frame(moments(strokes(a)))
        fb = frame(moments(strokes(b)))
        A = affine_map(fb, fa)  # maps ref frame <- other frame
        rw, ok = warp(residual(b), A, a.shape)
        ok &= np.abs(warp(b, A, a.shape)[0]) < 250  # ignore outside
        val = ncc_in(residual(a), rw, ok)
        print(f"{ref.split('/')[-1]} <- {other.split('/')[-1]}  overlap={ok.mean():.3f}  NCC_aligned={val:+.4f}")


if __name__ == "__main__":
    main()
