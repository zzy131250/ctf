#!/bin/bash
# Local check of the frontend half of the Duplex chain.
#   backend (fake apache) on 127.0.0.1:80   <- needs root
#   proxy (the handout binary) under qemu on :8080
#   then push both framings through and dump what the backend saw
set -u
cd "$(dirname "$0")"
LOG=/tmp/duplex_backend.log
rm -f "$LOG"

sudo -n python3 backend_only.py 80 "$LOG" &
BACK=$!
sleep 2
qemu-x86_64-static -L /usr/x86_64-linux-gnu ./duplex/proxy > /tmp/duplex_proxy.log 2>&1 &
PROX=$!
sleep 1.5

python3 - <<'PY'
import socket, sys, time
sys.path.insert(0, '.')
import exploit

for name, payload in (("chunked", exploit.variant_chunked()),
                      ("identity", exploit.variant_identity())):
    s = socket.create_connection(("127.0.0.1", 8080), timeout=10)
    s.settimeout(4)
    s.sendall(payload)
    try:
        resp = s.recv(65536)
    except socket.timeout:
        resp = b"<no reply>"
    s.close()
    print(f"=== {name}: frontend replied {resp[:120]!r}")
    time.sleep(0.5)
PY

sleep 0.5
kill $PROX 2>/dev/null
sudo -n pkill -f backend_only.py 2>/dev/null
echo "===== what the backend received ====="
cat "$LOG"
