ct_hex = "2d55090d4f576242655d24030705490250210748502d54111f4450065f0f010704041d5f6024485b500851457a5201384c68255b000613351141070859560b4a1c03094a0e1a505007471d0e0749080a5442074818160e48170f56"
key = "#!s3kur1ty"
ct = bytes.fromhex(ct_hex)
out = []
for i, c in enumerate(ct):
    k = ord(key[i % len(key)])
    t = c ^ k
    out.append((t - 67) % 128)
s = bytes(out).decode()
print(repr(s))
