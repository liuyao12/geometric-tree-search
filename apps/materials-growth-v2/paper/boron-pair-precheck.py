"""Restricted geometry-only pair-support diagnostic, not free growth.

Use all minimum-image unordered pairs below a data-scaled radius; cluster their
lengths with bounded bin width. Endpoint-symmetric shared weights are learned by
LP and accepted only after exact rational substitution. No chemistry is input.
The periodic quotient excludes distinct images of the same atom pair, so these
tests are explicitly finite-quotient controls, not an infinite-lift certificate.
"""
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from ase import Atoms
from scipy.optimize import linprog

spec = importlib.util.spec_from_file_location('marks', Path(__file__).with_name('presearch-markings.py'))
marks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(marks)


def run(config, scale, width):
    atoms = Atoms('B' * config['atoms'], positions=config['positions'], cell=config['cell'], pbc=True)
    n = len(atoms)
    d = atoms.get_all_distances(mic=True)
    np.fill_diagonal(d, np.inf)
    radius = float(np.median(d.min(axis=1))) * scale
    pairs = sorted((float(d[a,b]),a,b) for a in range(n) for b in range(a+1,n) if d[a,b] <= radius)
    groups = []
    for distance,a,b in pairs:
        if not groups or distance-groups[-1][0][0] > width:
            groups.append([])
        groups[-1].append((distance,a,b))
    k = len(groups)
    A = np.zeros((n,k), dtype=int)
    incidence = [[] for _ in range(n)]
    for j,g in enumerate(groups):
        for _,a,b in g:
            A[a,j] += 1; A[b,j] += 1
            incidence[a].append(j); incidence[b].append(j)
    # Maximize the minimum positive shared contribution eta.
    eq = np.column_stack((A,np.zeros(n)))
    ub = np.column_stack((-np.eye(k),np.ones(k)))
    result = linprog([0]*k+[-1], A_ub=ub, b_ub=np.zeros(k),
                     A_eq=eq, b_eq=np.ones(n), bounds=[(0,1)]*(k+1), method='highs')
    out = dict(file=config['file'],radiusScale=scale,lengthBinWidth=width,radius=radius,
               pairs=len(pairs),types=k,solverStatus=result.message)
    if not result.success:
        return dict(out,status='restricted LP infeasible' if result.status==2 else 'unknown')
    w = [Fraction(float(x)).limit_denominator(1000000) for x in result.x[:-1]]
    exact = all(sum(int(A[p,j])*w[j] for j in range(k)) == 1 for p in range(n))
    if not exact or min(w) <= 0:
        return dict(out,status='unknown: rational verification or positive-support gate failed')
    labels = marks.equality_labels(k,incidence)
    placements = [{'t':{a:str(w[j]),b:str(w[j])},'m':{a:labels[j],b:labels[j]}}
                  for j,g in enumerate(groups) for _,a,b in g]
    check = marks.precheck(list(range(n)),placements)
    assert check['valid']
    parents = list(range(n))
    def root(a):
        while parents[a]!=a:
            a=parents[a]
        return a
    for _,a,b in pairs:
        parents[root(a)] = root(b)
    return dict(out,status='exact finite-quotient t/m precheck passed',weights=list(map(str,w)),
                scalarMarkClasses=len(set(labels)),positiveComponents=len({root(a) for a in range(n)}),
                precheck=check,blindGrowthTested=False)


if __name__ == '__main__':
    data=json.loads(Path(sys.argv[1]).read_text())
    results=[]
    for config in data['results']:
        for scale in (1.15,1.35,1.6):
            for width in (.01,.05):
                result=run(config,scale,width)
                results.append(result)
                print(json.dumps({k:v for k,v in result.items() if k!='weights'}),flush=True)
    Path(sys.argv[2]).write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
