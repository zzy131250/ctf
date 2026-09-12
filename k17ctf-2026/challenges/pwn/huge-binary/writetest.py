import re,sys
from rprobe import run
# each test: write count 0xF0F via %A$hn to the address = value(argA),
# then print the arg whose SLOT we believe that address is.
tests=[
 # (writer, expected_slot_arg, label)
 (20,51,'rbp+0xf0 -> slot of 51'),
 (50,52,'rbp+0xf8 -> slot of 52'),
 (38,53,'rbp+0x100 -> slot of 53'),
 (46,53,'rbp+0x100 -> slot of 53 (via 46)'),
 (35,54,'rbp+0x108 -> slot of 54'),
 (27,56,'rbp+0x118 -> slot of 56'),
]
for w,rd,label in tests:
    fmt='%%1$3855c%%%d$hn.%%%d$p'%(w,rd)
    try:
        lk,out=run('1',fmt,'B')
        v=re.findall(r'0x[0-9a-f]+|\(nil\)',out)
        print('%-34s fmt=%-20s -> %s'%(label,fmt,v))
    except Exception as e:
        print(label,'ERR',e)
