import re, sys
sys.path.insert(0, 'blowfish')
from client import Conn

def get_data():
    c = Conn()
    d = c.recv_until(b'? ').decode()
    c.close()
    fish = re.search(r'Fish: ([0-9a-f]+)', d).group(1)
    sig = re.search(r'Signature: ([0-9a-f]+)', d).group(1)
    return fish, sig

f1, s1 = get_data()
f2, s2 = get_data()
b1 = bytes.fromhex(f1); b2 = bytes.fromhex(f2)
print("len fish1", len(b1), "len fish2", len(b2))
print("json1 head", b1[8:60])
print("json2 head", b2[8:60])
n = len(s1)//64
print("num digests sig1", n, "len sig1", len(s1))
# compare block digests
same = [i for i in range(min(len(s1),len(s2))//64) if s1[i*64:(i+1)*64]==s2[i*64:(i+1)*64]]
print("num equal digests:", len(same), same[:20])
# print block contents
for i in range(0, min(6, n)):
    print(i, b1[i*8:(i+1)*8])
