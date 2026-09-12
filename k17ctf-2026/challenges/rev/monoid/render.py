palette = " .-:=+*#%@"
cx, cy, maxIter, width, height = -0.745643887, 0.113825904, 180, 96, 32

def render(cx, cy, maxIter, width, height):
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            zr = -1.8 + 3.6 * x / (width - 1)
            zi = (-1.0 + 2.0 * y / (height - 1)) * 0.5
            n = 0
            while True:
                if (zr*zr + zi*zi) ** 0.5 > 2.0:
                    break
                if n >= maxIter:
                    break
                zr, zi = zr*zr - zi*zi + cx, 2*zr*zi + cy
                n += 1
            idx = min(len(palette) - 1, (n * len(palette)) // (maxIter + 1))
            row.append(palette[idx])
        rows.append("".join(row))
    return "\n".join(rows) + "\n"

mine = render(cx, cy, maxIter, width, height)
ref = open("out.txt").read()
print("MATCH:", mine == ref)
if mine != ref:
    ml, rl = mine.split("\n"), ref.split("\n")
    for i,(a,b) in enumerate(zip(ml,rl)):
        if a != b:
            print("row", i, "len", len(a), len(b))
            print("mine:", a)
            print("ref :", b)
            break
else:
    open("repro.txt","w").write(mine)
