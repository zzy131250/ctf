#!/usr/bin/env python3
"""Look at the raw noise: what does a residual actually look like?"""
import numpy as np
from PIL import Image, ImageFilter


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float32)


def blur5(a):
    k = np.ones((5, 5), dtype=np.float32)
    k /= k.sum()
    P = np.pad(a, 2, mode="edge")
    out = np.zeros_like(a)
    for dy in range(5):
        for dx in range(5):
            out += k[dy, dx] * P[dy : dy + a.shape[0], dx : dx + a.shape[1]]
    return out


def res(p):
    a = load(p)
    return a - blur5(a)


if __name__ == "__main__":
    for name, p in [
        ("A0", "drive/reference/A/ref_000.png"),
        ("A1", "drive/reference/A/ref_001.png"),
        ("B0", "drive/reference/B/ref_000.png"),
    ]:
        r = res(p)
        c = r[400:1200, 400:1200]
        Image.fromarray(np.clip(128 + c * 20, 0, 255).astype(np.uint8)).save(f"res_{name}.png")
        # histogram of the flat background corner
        corner = r[0:500, 0:500]
        print(name, "std", round(float(r.std()), 3), "corner std", round(float(corner.std()), 3))
    print("ok")
