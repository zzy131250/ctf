import pickle, pickletools

class EncryptedKV:
    def __init__(self, secret):
        self.secret = secret
        self.d = {}
    def __getitem__(self, key):
        num: int = (self.d[key] ^ self.secret)
        # nb: original ekv.py omitted byteorder, which defaulted to 'big'
        # before Python 3.11 made it mandatory.
        return num.to_bytes(-(num.bit_length() // -8), 'big').decode()
    def __setitem__(self, key, value):
        self.d[key] = int.from_bytes(value.encode()) ^ self.secret

raw = open('out.pkl.part','rb').read()
assert raw[0:2] == b'\x80\x04' and raw[2] == 0x95
body = raw[:2] + raw[11:]                      # strip FRAME
cut = body.index(b'\x8c\x21admin password')    # drop valueless last key
rebuilt = body[:cut] + b'uub.'                 # SETITEMS, SETITEMS, BUILD, STOP

obj = pickle.loads(rebuilt)
print("secret =", obj.secret)
print()
for k in obj.d:
    print(f"{k!r:48} -> {obj[k]!r}")
