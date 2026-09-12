#!/usr/bin/env python3
"""Hunt for any per-image statistic that separates camera A from camera B."""
import glob
import os

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive")


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float32)


def blur3(a):
    P = np.pad(a, 1, mode="edge")
    return (
        P[:-2, :-2] + P[:-2, 1:-1] + P[:-2, 2:]
        + P[1:-1, :-2] + P[1:-1, 1:-1] + P[1:-1, 2:]
        + P[2:, :-2] + P[2:, 1:-1] + P[2:, 2:]
    ) / 9.0


def stats(path):
    a = load(path)
    r = a - blur3(a)
    # "flat" = locally smooth in the *image* (no drawn stroke nearby)
    b = blur3(a)
    flat = np.abs(a - b) < 1.0
    rf = r[flat]
    rf = rf - rf.mean()
    s = rf.std()
    kurt = float((rf ** 4).mean() / (s ** 4 + 1e-12))
    # residual autocorrelation inside flat areas
    m = flat
    ax = float((r[:, :-1] * r[:, 1:])[m[:, :-1] & m[:, 1:]].mean()) / (r.std() ** 2 + 1e-12)
    ay = float((r[:-1, :] * r[1:, :])[m[:-1, :] & m[1:, :]].mean()) / (r.std() ** 2 + 1e-12)
    ad = float((r[:-1, :-1] * r[1:, 1:])[m[:-1, :-1] & m[1:, 1:]].mean()) / (r.std() ** 2 + 1e-12)
    # sharpness across strokes
    gx = np.abs(np.diff(a, axis=1))
    sharp = float(np.percentile(gx, 99.9))
    # brightness of the four corners (vignetting / gradient)
    c = 200
    corners = [a[:c, :c].mean(), a[:c, -c:].mean(), a[-c:, :c].mean(), a[-c:, -c:].mean()]
    # saturated pixels
    sat = float((a > 250).mean() + (a < 3).mean())
    return dict(noise_std=s, kurt=kurt, ac_x=ax, ac_y=ay, ac_d=ad, sharp=sharp,
                c00=corners[0], c01=corners[1], c10=corners[2], c11=corners[3], sat=sat)


if __name__ == "__main__":
    rows = []
    for cam in "AB":
        for p in sorted(glob.glob(os.path.join(ROOT, "reference", cam, "*.png"))):
            st = stats(p)
            rows.append((cam, os.path.basename(p), st))
    for cam in "AB":
        for p in sorted(glob.glob(os.path.join(ROOT, "queries", "*.png"))):
            st = stats(p)
            rows.append((cam, os.path.basename(p), st))
    keys = list(rows[0][2].keys())
    print("cam  file       " + " ".join(f"{k:>9s}" for k in keys))
    for cam, name, st in rows:
        print(f"{cam}    {name:10s} " + " ".join(f"{st[k]:9.3f}" for k in keys))
