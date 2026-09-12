import struct

W, H = 120, 82
d = open('etchasketch','rb').read()
brush_r = struct.unpack_from('<i', d, 0x3020)[0]   # file off of 0x4020
pts = list(struct.unpack_from('<325i', d, 0x2020))
print("brush_r =", brush_r)

canvas = [[0]*W for _ in range(H)]

def dab(cx, cy):
    r = brush_r
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            x = cx + dx
            y = cy + dy
            if 0 <= x <= W-1 and 0 <= y <= H-1:
                canvas[y][x] = 1

def line(p1, p2):  # packed (y<<16)|x
    x1 = (p1 & 0xffff); y1 = (p1 >> 16) & 0xffff
    x2 = (p2 & 0xffff); y2 = (p2 >> 16) & 0xffff
    # signed 16
    def s16(v): return v-0x10000 if v & 0x8000 else v
    x1, y1, x2, y2 = s16(x1), s16(y1), s16(x2), s16(y2)
    dx = abs(x2 - x1); dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx + dy
    cx, cy = x1, y1
    dab(cx, cy)
    while not (cx == x2 and cy == y2):
        e2 = 2*err
        if e2 >= dy:
            err += dy
            cx += sx
        if e2 <= dx:
            err += dx
            cy += sy
        dab(cx, cy)

prev = -1
for i in range(325):
    v = pts[i]
    if (v & 0xffff) == 0xfffe:
        break
    if not (v & 0x8000) and not (prev & 0x8000):
        line(prev, v)
    prev = v

out = []
for y in range(H):
    out.append(''.join('#' if canvas[y][x] else ' ' for x in range(W)))
text = '\n'.join(out) + '\n'
open('sim_out.txt','w').write(text)
print(text)
