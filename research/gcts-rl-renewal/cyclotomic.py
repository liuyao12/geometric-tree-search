"""Exact integral arithmetic in Z[zeta_5], without arrows or substitution data."""
from itertools import product

ZERO = (0,0,0,0)
ONE = (1,0,0,0)
ZETA = (0,1,0,0)

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def neg(a): return tuple(-x for x in a)
def mul(a,b):
    coeff = [0]*7
    for i,x in enumerate(a):
        for j,y in enumerate(b): coeff[i+j] += x*y
    # z^4 = -(1+z+z^2+z^3), monic exact reduction.
    for degree in range(6,3,-1):
        value = coeff[degree]
        for j in range(4): coeff[degree-4+j] -= value
    return tuple(coeff[:4])

def power(a,n):
    out = ONE
    for _ in range(n): out = mul(out,a)
    return out

def conjugate(a):
    out = ZERO
    for i,x in enumerate(a): out = add(out,tuple(x*y for y in power(ZETA,(5-i)%5)))
    return out

PHI = (0,0,-1,-1)
RHOMBS = {
    "thick":{"vertices":(ZERO,ONE,add(ONE,ZETA),ZETA),"angles":(2,3,2,3)},
    "thin":{"vertices":(ZERO,ONE,add(ONE,neg(power(ZETA,2))),neg(power(ZETA,2))),"angles":(1,4,1,4)}
}

def audit():
    examples = tuple(product(range(-1,2),repeat=4))
    checked = 0
    for a in examples:
        assert conjugate(conjugate(a))==a
        for b in examples:
            assert conjugate(mul(a,b))==mul(conjugate(a),conjugate(b))
            assert mul(a,b)==mul(b,a)
            checked += 1
    assert power(ZETA,5)==ONE
    assert mul(PHI,PHI)==add(PHI,ONE)
    assert mul(PHI,add(PHI,neg(ONE)))==ONE
    return {"exact_pair_checks":checked,"basis_rank":4,"minimal_polynomial":[1,1,1,1,1],
            "phi":PHI,"phi_identity_verified":True,"rhombs":RHOMBS,
            "status":"exact arithmetic and unmarked vertex data; faithful point model pending",
            "physical_embedding":"dense module; not a discrete planar lattice"}
