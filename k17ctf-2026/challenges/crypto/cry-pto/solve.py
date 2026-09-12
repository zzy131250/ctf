#!/usr/bin/env python3
# cry-pto: sig is a GF(2)-linear map M: {0,1}^64 -> {0,1}^128
#   res bit = parity(row_i & msg)  =>  M(a xor b) = M(a) xor M(b)
# Query q = user xor root (q != root, allowed). Then
#   M(root) = M(user) xor M(q) = user_sig xor query_sig
import socket, sys

HOST, PORT = "chal.secso.cc", 2000
user = b"babyuser"
root = b"chadr00t"
assert len(user) == 8 and len(root) == 8

q = bytes(a ^ b for a, b in zip(user, root))
assert q != root

s = socket.create_connection((HOST, PORT), timeout=30)
f = s.makefile("rwb")

line = f.readline().decode()
print("[*]", line.strip())
user_sig = bytes.fromhex(line.split("signature:")[1].strip())
print("[*] user_sig =", user_sig.hex())

f.write(q.hex().encode() + b"\n")
f.flush()
line = f.readline().decode()
print("[*]", line.strip())
query_sig = bytes.fromhex(line.split("signature:")[1].strip())
print("[*] query_sig =", query_sig.hex(), " (q =", q.hex(), ")")

attempt = bytes(a ^ b for a, b in zip(user_sig, query_sig))
assert len(attempt) == 16
print("[*] forged root sig =", attempt.hex())

f.write(attempt.hex().encode() + b"\n")
f.flush()
rest = f.read().decode(errors="replace")
print("[*] response:", rest)
s.close()

import re
m = re.search(r"K17\{[^}]*\}", rest)
print("[+] FLAG:", m.group(0) if m else "NOT FOUND")
