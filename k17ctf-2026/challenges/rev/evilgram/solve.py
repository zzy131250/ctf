#!/usr/bin/env python3
"""
Evilgram (k17ctf, rev) — offline solver.

Input : evilgram.html from handout.zip (a Plotly 3D voxel animation, 128 frames of a
        4x4x4 binary map produced by a 256-state block cellular automaton).
Output: the plaintext message (contains the flag).

Run:  python3 solve.py path/to/evilgram.html
"""
import sys, re, json, math
import numpy as np

N = 4  # map_size


# ---------------------------------------------------------------- 1. parse HTML
def parse_frames(path):
    d = open(path, encoding="utf-8").read()
    i = d.find("Plotly.addFrames")
    start = d.find("[", i)
    depth = 0
    for k in range(start, len(d)):
        if d[k] == "[":
            depth += 1
        elif d[k] == "]":
            depth -= 1
            if depth == 0:
                end = k + 1
                break
    return json.loads(d[start:end])


# ------------------------------------------------- 2. frames -> 4x4x4 bool maps
def frames_to_maps(frames):
    maps = []
    for f in frames:
        x = np.array(f["data"][0]["x"])
        y = np.array(f["data"][0]["y"])
        z = np.array(f["data"][0]["z"])
        # build_voxel_mesh emits 8 consecutive cube vertices per voxel; the first
        # one is the voxel origin. pad_vertices() zero-pads the tail to max_voxels,
        # i.e. adds a run of (0,0,0) origins that must be dropped.
        origins = list(zip(z[::8].tolist(), y[::8].tolist(), x[::8].tolist()))
        pad = 0
        for o in reversed(origins):
            if o == (0, 0, 0):
                pad += 1
            else:
                break
        m = np.zeros((N, N, N), dtype=np.uint8)
        for (zz, yy, xx) in origins[: len(origins) - pad]:
            m[zz][yy][xx] = 1
        maps.append(m)
    return np.array(maps)


def block_state(m, z, y, x):
    g = lambda a, b, c: int(m[a % N][b % N][c % N])
    return (g(z, y, x)
            + 2 * g(z, y, x + 1)
            + 4 * g(z, y + 1, x)
            + 8 * g(z, y + 1, x + 1)
            + 16 * g(z + 1, y, x)
            + 32 * g(z + 1, y, x + 1)
            + 64 * g(z + 1, y + 1, x)
            + 128 * g(z + 1, y + 1, x + 1))


# ------------------------------------- 3. recover the ruleset (a permutation)
def recover_ruleset(maps):
    rules = {}
    for step in range(1, maps.shape[0]):
        ox = step & 1
        oy = 1 if step & 2 else 0
        oz = 1 if step & 4 else 0
        before, after = maps[step - 1], maps[step]
        for xb in range(2):
            for yb in range(2):
                for zb in range(2):
                    x, y, z = xb * 2 + ox, yb * 2 + oy, zb * 2 + oz
                    s = block_state(before, z, y, x)
                    t = block_state(after, z, y, x)
                    assert rules.setdefault(s, t) == t, "inconsistent automaton"
    assert len(rules) == 256 and sorted(rules.values()) == list(range(256))
    return [rules[i] for i in range(256)]


# --------------------------------- 4. invert rule = encode_msg_to_ruleset(msg)
def ruleset_to_message(ruleset):
    l = list(range(256))
    digits = [0] * 256          # digits[i] = factoradic digit d_i
    for j in range(256):        # ruleset[j] was popped with skip d_{255-j}
        sk = l.index(ruleset[j])
        digits[255 - j] = sk
        l.pop(sk)
    num = sum(d * math.factorial(i) for i, d in enumerate(digits))
    return num.to_bytes((num.bit_length() + 7) // 8, "big")


if __name__ == "__main__":
    frames = parse_frames(sys.argv[1])
    maps = frames_to_maps(frames)
    ruleset = recover_ruleset(maps)
    print(ruleset_to_message(ruleset).decode())
