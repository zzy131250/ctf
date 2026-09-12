import json, re
from Crypto.Cipher import Blowfish
from hashlib import sha256
from random import choice as rand_choice, randbytes

ALPHA = "abcdefghijhklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class LocalOracle:
    def __init__(self, flag="K17{local_test_flag}"):
        self.SECRET_KEY = randbytes(8)
        self.SECRET_SIGNING_KEY = randbytes(8)
        self.FLAG = flag
        your_fish = {"admin": "ABSOLUTELY NOT"}
        while len(your_fish) < 50:
            k = "".join(rand_choice(ALPHA) for _ in range(8))
            v = "".join(rand_choice(ALPHA) for _ in range(8))
            your_fish[k] = v
            if len(your_fish) != len(set(your_fish)):  # never triggers
                pass
        # ensure 50 unique keys
        your_fish = {"admin": "ABSOLUTELY NOT"}
        seen = set()
        while len(your_fish) < 50:
            k = "".join(rand_choice(ALPHA) for _ in range(8))
            if k in seen:
                continue
            seen.add(k)
            v = "".join(rand_choice(ALPHA) for _ in range(8))
            your_fish[k] = v
        self.iv = randbytes(8)
        self.iv_fish = self.iv + json.dumps(your_fish).encode()

    def pad(self, data):
        if len(data) % 8 != 0:
            data += b'\x00' * (8 - len(data) % 8)
        return data

    def unpad(self, data):
        return data.rstrip(b'\x00')

    def sign(self, raw):
        return "".join(sha256(self.SECRET_SIGNING_KEY + raw[i:i+8]).hexdigest()
                       for i in range(0, len(raw), 8))

    def initial(self):
        return self.iv_fish, self.sign(self.iv_fish)

    def blow(self, plaintext_hex, sig_hex):
        if self.sign(bytes.fromhex(plaintext_hex)) != sig_hex:
            return None
        p = bytes.fromhex(plaintext_hex)
        iv = p[:8]
        raw = iv + Blowfish.new(self.SECRET_KEY, Blowfish.MODE_CBC, iv=iv).encrypt(self.pad(p[8:]))
        return raw.hex(), self.sign(raw)

    def unblow(self, ct_hex, sig_hex):
        if self.sign(bytes.fromhex(ct_hex)) != sig_hex:
            return None
        c = bytes.fromhex(ct_hex)
        iv = c[:8]
        try:
            raw = iv + self.unpad(Blowfish.new(self.SECRET_KEY, Blowfish.MODE_CBC, iv=iv).decrypt(c[8:]))
        except Exception:
            return None
        return raw.hex(), self.sign(raw)

    def is_admin(self, plaintext_hex):
        try:
            return json.loads(bytes.fromhex(plaintext_hex)[8:]).get("admin") is True
        except Exception:
            return False


import socket

class RemoteOracle:
    def __init__(self, host='chal.secso.cc', port=2001):
        self.s = socket.create_connection((host, port), timeout=30)
        self.buf = b''

    def _read_until(self, marker, timeout=30):
        self.s.settimeout(timeout)
        while marker not in self.buf:
            d = self.s.recv(65536)
            if not d:
                break
            self.buf += d
        i = self.buf.find(marker)
        if i < 0:
            out, self.buf = self.buf, b''
            return out
        i += len(marker)
        out, self.buf = self.buf[:i], self.buf[i:]
        return out

    def _send(self, data):
        if isinstance(data, str):
            data = data.encode()
        self.s.sendall(data)

    def initial(self):
        d = self._read_until(b'? ')
        fish = re.search(rb'Fish: ([0-9a-f]+)', d).group(1).decode()
        sig = re.search(rb'Signature: ([0-9a-f]+)', d).group(1).decode()
        return bytes.fromhex(fish), sig

    def _parse(self, d):
        m = re.search(rb'went swimmingly: ([0-9a-f]*)\nSignature: ([0-9a-f]*)', d)
        if m:
            return m.group(1).decode(), m.group(2).decode()
        m = re.search(rb'bass-sides the point: ([0-9a-f]*)\nSignature: ([0-9a-f]*)', d)
        if m:
            return m.group(1).decode(), m.group(2).decode()
        return None

    def blow(self, plaintext_hex, sig_hex):
        self._send(b'1\n')
        self._read_until(b'Enter fish: ')
        self._send(plaintext_hex + '\n')
        self._read_until(b'Sign the fish: ')
        self._send(sig_hex + '\n')
        d = self._read_until(b'? ')
        return self._parse(d)

    def unblow(self, ct_hex, sig_hex):
        self._send(b'2\n')
        self._read_until(b'Enter up-blown/unup-unblown fish: ')
        self._send(ct_hex + '\n')
        self._read_until(b'Sign the fish: ')
        self._send(sig_hex + '\n')
        d = self._read_until(b'? ')
        return self._parse(d)

    def submit_admin(self, plaintext_hex, sig_hex):
        # kind of the same as blow but we look for the flag
        self._send(b'1\n')
        self._read_until(b'Enter fish: ')
        self._send(plaintext_hex + '\n')
        self._read_until(b'Sign the fish: ')
        self._send(sig_hex + '\n')
        d = b''
        try:
            d = self._read_until(b'K17{', timeout=15)
            self.s.settimeout(5)
            while b'}' not in d[d.find(b'K17{'):]:
                chunk = self.s.recv(4096)
                if not chunk:
                    break
                d += chunk
        except Exception:
            pass
        m = re.search(rb'(K17\{[^}]*\})', d)
        return (m.group(1).decode() if m else None), d
