#!/usr/bin/env python3
"""Final classifier for k17ctf 'verify you are human': PRNU match to camera A/B."""
import glob
import os

import numpy as np
from PIL import Image
import pywt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive")


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float64)


def denoise(a):
    coeffs = pywt.wavedec2(a, "db8", level=4)
    out = [coeffs[0]]
    for (cH, cV, cD) in coeffs[1:]:
        new = []
        for c in (cH, cV, cD):
            sn2 = (np.median(np.abs(c)) / 0.6745) ** 2
            m = np.abs(c) ** 2
            P = np.pad(m, 1, mode="edge")
            loc = (
                P[:-2, :-2] + P[:-2, 1:-1] + P[:-2, 2:]
                + P[1:-1, :-2] + P[1:-1, 1:-1] + P[1:-1, 2:]
                + P[2:, :-2] + P[2:, 1:-1] + P[2:, 2:]
            ) / 9.0
            new.append(c * np.maximum(0.0, 1.0 - sn2 / (loc + 1e-12)))
        out.append(tuple(new))
    return pywt.waverec2(out, "db8")


def residual(path):
    a = load(path)
    d = denoise(a)
    r = (a - d[: a.shape[0], : a.shape[1]]).astype(np.float32)
    r -= r.mean()
    return r / max(r.std(), 1e-9)


def fp(paths):
    acc = None
    for p in paths:
        r = residual(p)
        acc = r if acc is None else acc + r
        del r
    acc /= len(paths)
    acc -= acc.mean()
    return acc / max(acc.std(), 1e-9)


def main():
    ka = fp(sorted(glob.glob(os.path.join(ROOT, "reference", "A", "*.png"))))
    kb = fp(sorted(glob.glob(os.path.join(ROOT, "reference", "B", "*.png"))))
    print(f"fingerprints built: A std={ka.std():.3f}  B std={kb.std():.3f}", flush=True)

    ans = []
    for p in sorted(glob.glob(os.path.join(ROOT, "queries", "*.png"))):
        r = residual(p)
        sa, sb = float((r * ka).mean()), float((r * kb).mean())
        pick = "A" if sa > sb else "B"
        ans.append(pick)
        print(f"{os.path.basename(p)}  A={sa:+.5f}  B={sb:+.5f}  -> {pick}   |A-B|={abs(sa-sb):.5f}",
              flush=True)
        del r
    s = "".join(ans)
    print("\nanswer:", s)
    print("flag  : K17{%s}" % s)


if __name__ == "__main__":
    main()
