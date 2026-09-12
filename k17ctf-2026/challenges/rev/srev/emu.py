import struct, sys
raw = open('srev','rb').read()
BASE = 0x400000
def rdq(v): return struct.unpack_from('<Q', raw, v-BASE)[0]
def rddw(v): return struct.unpack_from('<i', raw, v-BASE)[0]

NUMCTX = 291
CTXBASE = 0x403994
CTXSZ = 248
ctxs = [(rdq(CTXBASE+i*CTXSZ+0xa8), rdq(CTXBASE+i*CTXSZ+0x90)) for i in range(NUMCTX)]

PROGBASE = 0x4020f8
PROGSZ = 252
NPROG = 25
progs = [bytearray(raw[PROGBASE+i*PROGSZ+4-BASE : PROGBASE+i*PROGSZ+PROGSZ-BASE]) for i in range(NPROG)]
assert all(len(p)==248 for p in progs)

REGT = [0x00,0x28,0x30,0x38,0x40,0x48,0x50,0x58,0x60,0x68,0x70,0x78,0x80,0x88,0x98,0xa8]
M64 = (1<<64)-1

def getq(fr, off): return struct.unpack_from('<Q', fr, off)[0]
def setq(fr, off, v): struct.pack_into('<Q', fr, off, v & M64)

class Abort(Exception): pass

def sgn(v):
    return v-(1<<64) if v >= (1<<63) else v

def compare(regval, value, cmpop):
    # jump table @0x402020: cmpop 1..6
    if cmpop == 1: return 1 if value == regval else 0
    if cmpop == 2: return 1 if value != regval else 0
    if cmpop == 3: return 1 if (regval & M64) <  (value & M64) else 0
    if cmpop == 4: return 1 if (regval & M64) >= (value & M64) else 0
    if cmpop == 5: return 1 if sgn(regval) <  sgn(value) else 0
    if cmpop == 6: return 1 if sgn(regval) >= sgn(value) else 0
    raise Abort("bad cmp")

def compare_call(fr, arg):
    reg = (arg>>28)&0xf
    cmpop = (arg>>24)&0xf
    value = (arg>>32) & 0xffffffff
    if reg == 0 or cmpop == 0: return 1
    if cmpop > 6: raise Abort("cmpop>6")
    return compare(getq(fr, REGT[reg]), value, cmpop)

def ror64(v, n):
    n &= 0x3f
    if n == 0: return v
    return ((v >> n) | (v << (64-n))) & M64

class VM:
    def __init__(self):
        self.frames = []
        self.F = 0
        self.steps = 0
    @property
    def depth(self): return len(self.frames)
    def step(self):
        self.steps += 1
        if self.F < 0 or self.F >= NUMCTX: raise Abort("F out of range: %d"%self.F)
        op, arg = ctxs[self.F]
        fr = self.frames
        d = len(fr)
        if op == 1:
            mask = arg & 0xffff
            k = (arg>>16)&0xf
            if d <= 1: raise Abort("op1 depth<=1")
            r8 = getq(fr[d-1], REGT[k]) if k else 0
            top = fr[d-1]; sec = fr[d-2]
            for r in range(1,16):
                if mask & (1<<r):
                    setq(sec, REGT[r], getq(top,REGT[r]) + r8)
            fr.pop()
        elif op == 2:
            do = (d==0) or compare_call(fr[d-1], arg)
            if do:
                idx = arg & 0xffffff
                if idx >= NPROG: raise Abort("prog idx")
                if len(fr) >= 256: raise Abort("depth256 op2")
                fr.append(bytearray(progs[idx]))
        elif op == 3:
            if compare_call(fr[d-1], arg):
                target = arg & 0xffffff
                if len(fr) >= 256: raise Abort("depth256 op3")
                if target >= len(fr): raise Abort("op3 target>=depth")
                fr.append(bytearray(fr[len(fr)-1-target]))
        elif op == 4:
            if d < arg: raise Abort("op4 depth<arg")
            del fr[len(fr)-int(arg):]
        elif op in (5,6,7,8):
            dest = arg & 0xf
            if dest == 0: raise Abort("op%d dest0"%op)
            if d == 0: raise Abort("op%d depth0"%op)
            if (arg>>4)&1:
                val = arg>>8
            else:
                s = (arg>>8)&0xf
                if s == 0: raise Abort("op%d src0"%op)
                val = getq(fr[d-1], REGT[s])
            cur = getq(fr[d-1], REGT[dest])
            if op==5: nv = cur + val
            elif op==6: nv = cur - val
            elif op==7: nv = cur ^ val
            else: nv = ror64(cur, val)
            setq(fr[d-1], REGT[dest], nv)
        elif op == 9:
            return self.halt()
        else:
            raise Abort("bad op %d"%op)
        self.next()
        return None
    def next(self):
        d = len(self.frames)
        if d == 0:
            self.F += 1
        else:
            rip = getq(self.frames[d-1], 0xa8)
            if rip == 0:
                self.F += 1
            else:
                self.frames.pop()
                self.F = rip - 1
    def halt(self):
        d = len(self.frames)
        if d == 0:
            print("halt: empty stack"); return ('empty',)
        fr = self.frames[d-1]
        vals = [getq(fr, REGT[r]) for r in range(1,13)]
        ok = all(0x20 <= v <= 0x7e for v in vals)
        rdx = getq(fr, 0x88)
        regs = {r: getq(fr, REGT[r]) for r in range(1,16)}
        print("op9 at F=%d depth=%d vals=%r ok=%s rdx=%d" % (self.F, d, [chr(v) if 0x20<=v<0x7f else hex(v) for v in vals], ok, rdx))
        print("  regs:", {r:hex(regs[r]) for r in regs})
        if ok and rdx == 0:
            print("FLAG: K17{%s}" % ''.join(chr(v) for v in vals))
        return ('halt', vals, ok, rdx, regs)

if __name__ == '__main__':
    vm = VM()
    limit = int(sys.argv[1]) if len(sys.argv)>1 else 200000
    try:
        while vm.steps < limit:
            r = vm.step()
            if r is not None: break
        else:
            print("hit step limit", limit, "F=",vm.F,"depth=",vm.depth)
    except Abort as e:
        print("ABORT at step",vm.steps,"F=",vm.F,"depth=",vm.depth, e)
        if vm.frames:
            print("  top regs:", {r:hex(getq(vm.frames[-1],REGT[r])) for r in range(1,16)})
        for i in range(max(0,vm.F-8), min(NUMCTX, vm.F+4)):
            print("   ctx",i,ctxs[i])
