import resource, sys
from oracle import LocalOracle
from attack import Attacker, TARGET, TINT
o = LocalOracle()
at = Attacker(o)
print("atoms", len(at.atoms))
# test one xor3
a, b, c = at.atoms[0], at.atoms[1], at.atoms[2]
t = at.xor3(a, b, c)
print("xor3 ok:", hex(t[0]), "==", hex(a[0]^b[0]^c[0]))
print("mem MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
at.make_basis()
print("basis size", len(at.basis), "zero_exprs", len(at.zero_exprs))
ls = [len(z) for z in at.zero_exprs]
print("zero expr lens", sorted(ls)[:10], "max", max(ls) if ls else 0)
tv = [len(v[1]) for v in at.basis.values()]
print("basis leaf list lens: max", max(tv))
sol = at.solve(TINT)
print("solve ->", None if sol is None else len(sol))
print("mem MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
