import re, sys
sys.path.insert(0,'.')
from client import Conn
c=Conn(); d=c.recv_until(b'? ').decode(); c.close()
fish=bytes.fromhex(re.search(r'Fish: ([0-9a-f]+)',d).group(1))
iv=fish[:8]; js=fish[8:]
print("len fish",len(fish),"len json",len(js),"tail chunk len", len(fish)%8)
print(repr(js[:120]))
print("contains 'true':", b'true' in js)
chunks=[fish[i:i+8] for i in range(0,len(fish),8)]
for i,ch in enumerate(chunks[:14]):
    print(i, ch)
open('json.bin','wb').write(js)
open('fish.bin','wb').write(fish)
