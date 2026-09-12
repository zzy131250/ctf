#!/usr/bin/env python3
"""PRNU camera identification for k17ctf 'verify you are human'.

Residual = image - 3x3 median.  Fingerprint per camera = mean of the
zero-mean/unit-std residuals of its reference photos.  Query is matched by
normalised cross-correlation against each fingerprint.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive")
NORM = 511  # pixel-sum quantisation used everywhere; constant, cancels in NCC


def residual(path):
    im = Image.open(path).convert("L")
    a = np.asarray(im, dtype=np.float32)
    med = np.asarray(im.filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    r = a - med
    r -= r.mean()
    s = r.std()
    if s < 1e-6:
        return None
    return r / s


def fingerprint(paths):
    acc = None
    n = 0
    for p in paths:
        r = residual(p)
        if r is None:
            continue
        acc = r if acc is None else acc + r
        n += 1
        del r
    if acc is None:
        return None
    acc /= n
    acc -= acc.mean()
    acc /= max(acc.std(), 1e-9)
    return acc


def ncc(a, b):
    return float((a * b).mean())


def main():
    fps = {}
    for cam in ("A", "B"):
        refs = sorted(glob.glob(os.path.join(ROOT, "reference", cam, "*.png")))
        fps[cam] = fingerprint(refs)
        print(f"[*] camera {cam}: {len(refs)} refs, fp std={fps[cam].std():.4f}", flush=True)

    queries = sorted(glob.glob(os.path.join(ROOT, "queries", "*.png")))
    out = []
    for q in queries:
        r = residual(q)
        scores = {cam: ncc(r, fps[cam]) for cam in ("A", "B")}
        pick = "A" if scores["A"] > scores["B"] else "B"
        delta = abs(scores["A"] - scores["B"])
        out.append(pick)
        print(
            f"{os.path.basename(q)}  A={scores['A']:+.5f}  B={scores['B']:+.5f}  "
            f"-> {pick}  (delta {delta:.5f})",
            flush=True,
        )
        del r
    ans = "".join(out)
    print("\nanswer:", ans)
    print("flag  : K17{%s}" % ans)


if __name__ == "__main__":
    sys.exit(main())
