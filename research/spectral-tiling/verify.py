#!/usr/bin/env python3
"""Check the published data and heat-invariant deduction independently.

Uses the standard library only. Exact identities use rational arithmetic in Q(sqrt(3)).
Does not purport to validate the cited monotile theorem or bound FEM error.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Q3:
    a: F = F(0)
    b: F = F(0)
    def __add__(self,x):
        x = x if isinstance(x,Q3) else Q3(F(x))
        return Q3(self.a+x.a,self.b+x.b)
    __radd__ = __add__
    def __neg__(self): return Q3(-self.a,-self.b)
    def __sub__(self,x): return self+-coerce(x)
    def __rsub__(self,x): return coerce(x)+-self
    def __mul__(self,x):
        x = coerce(x)
        return Q3(self.a*x.a+3*self.b*x.b,self.a*x.b+self.b*x.a)
    __rmul__ = __mul__
    def __truediv__(self,x):
        x = coerce(x)
        return self*Q3(x.a,-x.b)*(1/(x.a*x.a-3*x.b*x.b))
    def __rtruediv__(self,x): return coerce(x)/self
    def __pow__(self,n):
        assert n>=0
        result = Q3(F(1))
        for _ in range(n): result = result*self
        return result
    def __float__(self): return float(self.a)+float(self.b)*math.sqrt(3)
    def record(self): return {'rational':str(self.a),'sqrt3_coefficient':str(self.b),'approx':float(self)}


def coerce(x): return x if isinstance(x,Q3) else Q3(F(x))


def main():
    data = json.loads((ROOT/'results.json').read_text())
    assert hashlib.sha256((ROOT/'compute.py').read_bytes()).hexdigest()==data['script_sha256']
    levels = sorted(data['levels'])
    largest_refinement_change = 0
    largest_residual = 0
    for case in data['cases']:
        points = case['vertices']
        edges = [(points[(i+1)%len(points)][0]-p[0],points[(i+1)%len(points)][1]-p[1])
                 for i,p in enumerate(points)]
        area = sum(p[0]*points[(i+1)%len(points)][1]-p[1]*points[(i+1)%len(points)][0]
                   for i,p in enumerate(points))/2
        perimeter = sum(math.hypot(*e) for e in edges)
        angles = [math.pi-math.atan2(edges[i-1][0]*e[1]-edges[i-1][1]*e[0],
                  edges[i-1][0]*e[0]+edges[i-1][1]*e[1]) for i,e in enumerate(edges)]
        corner = sum((math.pi**2-a*a)/(24*math.pi*a) for a in angles)
        r = case['r']
        assert math.isclose(area,math.sqrt(3)*(2+math.sqrt(3)*r+r*r),rel_tol=1e-12)
        assert math.isclose(perimeter,8+6*r,rel_tol=1e-12)
        assert math.isclose(corner,11/36,rel_tol=1e-12)
        for level in levels:
            m = case['meshes'][str(level)]
            assert math.isclose(m['mesh_area'],area,rel_tol=1e-12)
            assert all(math.isclose(v*area,w,rel_tol=1e-12)
                       for v,w in zip(m['eigenvalues'],m['area_eigenvalues']))
            assert all(x>0 for x in m['eigenvalues'])
            assert m['eigenvalues']==sorted(m['eigenvalues'])
            assert m['max_relative_residual']<1e-7
            largest_residual=max(largest_residual,m['max_relative_residual'])
        for lo,hi in zip(levels,levels[1:]):
            a = case['meshes'][str(lo)]['eigenvalues']
            b = case['meshes'][str(hi)]['eigenvalues']
            assert all(y<=x*(1+1e-9) for x,y in zip(a,b))
            if hi==max(levels): largest_refinement_change=max(largest_refinement_change,max(x/y-1 for x,y in zip(a,b)))
    square = data['square_control']
    exact = sorted(math.pi**2*(m*m+n*n) for m in range(1,10) for n in range(1,10))[:12]
    assert all(math.isclose(x,y,rel_tol=1e-13) for x,y in zip(exact,square['exact']))
    fine = square['meshes'][str(max(levels))]['eigenvalues']
    assert max(abs(x/y-1) for x,y in zip(fine,exact))<.002
    sqrt3 = Q3(F(0),F(1))
    rstar = (50*sqrt3-48)/(22*sqrt3-27)
    scale = 14/(8+6*rstar)
    A = lambda r:sqrt3*(2+sqrt3*r+r**2)
    P = lambda r:8+6*r
    assert A(Q3(F(1)))==scale**2*A(rstar)
    assert P(Q3(F(1)))==scale*P(rstar)
    # Independent exact angle list, with the straight-angle vertex omitted.
    angle_units = [F(1,2),F(2,3),F(3,2),F(2,3),F(1,2),F(4,3),F(1,2),
                   F(4,3),F(1,2),F(2,3),F(2,3),F(3,2),F(2,3)]
    C = sum((1/u-u)/24 for u in angle_units)
    assert C==F(11,36)
    receipt = {'status':'passed','date':'2026-10-07','checks':[
        'Source hash matches the executed experiment',
        'Independent polygon area, perimeter and corner calculations match every case',
        'Mesh areas and scale-normalized eigenvalues agree with polygon areas',
        'Nested refinements decrease every reported eigenvalue',
        'Residuals below threshold; square control agrees with exact low modes',
        'Area and perimeter equality proved exactly in Q(sqrt(3)) for heat-matched pair',
        'Heat corner constant proved exactly from rational angle multiples'],
        'max_fine_vs_previous_relative_change':largest_refinement_change,
        'max_eigensolver_relative_residual':largest_residual,
        'square_max_fine_relative_error':max(abs(x/y-1) for x,y in zip(fine,exact)),
        'heat_matched_pair':{'rstar':rstar.record(),'scale':scale.record(),
                             'common_area':A(Q3(F(1))).record(),'common_perimeter':14,
                             'common_corner_constant':str(C)},
        'limitations':'No rigorous continuum FEM error bounds. Known tiling labels rely on cited theorems. No full isospectrality or new aperiodicity proof is claimed.'}
    (ROOT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
