#!/usr/bin/env python3
"""Leave-one-out sanity check: does NCC(residual, K_cam) actually separate A from B?

For every reference photo we rebuild both fingerprints *without* that photo and
score it.  If the deltas for the A group are consistently positive and for the B
group consistently negative, the discriminative signal is real.
"""
import glob
import os

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive")


def residual(path):
    im = Image.open(path).convert("L")
    a = np.asarray(im, dtype=np.float32)
    m = np.asarray(im.filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    r = a - m
    r -= r.mean()
    return r / max(r.std(), 1e-9)


def fp(rs):
    acc = np.mean(rs, axis=0)
    acc -= acc.mean()
    return acc / max(acc.std(), 1e-9)


def main():
    refs = {c: sorted(glob.glob(os.path.join(ROOT, "reference", c, "*.png"))) for c in "AB"}
    rs = {c: [residual(p) for p in refs[c]] for c in "AB"}
    print("hold-out   cam  NCC_A     NCC_B     delta")
    ok = 0
    tot = 0
    for cam in "AB":
        for i, p in enumerate(refs[cam]):
            ka = fp([r for j, r in enumerate(rs["A"]) if not (cam == "A" and j == i)])
            kb = fp([r for j, r in enumerate(rs["B"]) if not (cam == "B" and j == i)])
            q = rs[cam][i]
            sa, sb = float((q * ka).mean()), float((q * kb).mean())
            d = sa - sb
            good = (d > 0) if cam == "A" else (d < 0)
            ok += good
            tot += 1
            print(f"{cam}{i}         {cam}    {sa:+.5f}  {sb:+.5f}  {d:+.5f}  {'ok' if good else 'WRONG'}")


if __name__ == "__main__":
    main()
