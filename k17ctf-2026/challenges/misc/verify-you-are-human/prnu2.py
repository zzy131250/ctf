#!/usr/bin/env python3
"""PRNU extraction with a Mihcak-style wavelet denoiser (db8, 4 levels).

The residual img - denoised(img) keeps sensor noise but suppresses scene edges
far better than a box filter, which is what the first attempt was choking on.
"""
import glob
import os
import sys

import numpy as np
import pywt
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive")
WAV = "db8"
LEV = 4


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float64)


def denoise(a):
    coeffs = pywt.wavedec2(a, WAV, level=LEV)
    out = [coeffs[0]]
    for (cH, cV, cD) in coeffs[1:]:
        new = []
        for c in (cH, cV, cD):
            sn = np.median(np.abs(c)) / 0.6745
            sn2 = sn * sn
            # local mean of squares over 3x3
            m = np.abs(c) ** 2
            loc = pywt.dwt  # placeholder, replaced below
            from numpy.lib.stride_tricks import sliding_window_view
            P = np.pad(m, 1, mode="edge")
            sw = sliding_window_view(P, (3, 3))
            loc = sw.mean(axis=(-1, -2))
            gain = np.maximum(0.0, 1.0 - sn2 / (loc + 1e-12))
            new.append(c * gain)
        out.append(tuple(new))
    return pywt.waverec2(out, WAV)


def residual(path):
    a = load(path)
    d = denoise(a)
    r = a - d[: a.shape[0], : a.shape[1]]
    r = r.astype(np.float32)
    r -= r.mean()
    s = r.std()
    return r / max(s, 1e-9)


def fp_from(rs):
    acc = np.mean(rs, axis=0)
    acc -= acc.mean()
    return acc / max(acc.std(), 1e-9)


def ncc(a, b):
    return float((a * b).mean())


def main():
    refs = {c: sorted(glob.glob(os.path.join(ROOT, "reference", c, "*.png"))) for c in "AB"}
    cache = {}
    for c in "AB":
        for p in refs[c]:
            cache[p] = residual(p)
            print("residual", p, flush=True)

    print("\n--- leave-one-out (zero shift) ---")
    ok = 0
    tot = 0
    for cam in "AB":
        for i, p in enumerate(refs[cam]):
            ka = fp_from([cache[q] for j, q in enumerate(refs["A"]) if not (cam == "A" and j == i)])
            kb = fp_from([cache[q] for j, q in enumerate(refs["B"]) if not (cam == "B" and j == i)])
            sa, sb = ncc(cache[p], ka), ncc(cache[p], kb)
            d = sa - sb
            good = (d > 0) if cam == "A" else (d < 0)
            ok += good
            tot += 1
            print(f"{os.path.basename(p)} ({cam})  A={sa:+.5f} B={sb:+.5f} delta={d:+.5f} {'ok' if good else 'WRONG'}")
    print(f"\nLOO accuracy: {ok}/{tot}")


if __name__ == "__main__":
    main()
