"""Independent modular rank plus exact certificates; synthetic RREF controls."""
import importlib.util
import json
import random
import sys
from fractions import Fraction as F
from pathlib import Path

spec = importlib.util.spec_from_file_location('weights', Path(__file__).with_name('boron-weight-identifiability.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def modrank(matrix, prime=1000003):
    a = [list(row) for row in matrix]
    rank = 0
    for c in range(len(a[0])):
        p = next((i for i in range(rank,len(a)) if a[i][c] % prime), None)
        if p is None:
            continue
        a[rank],a[p] = a[p],a[rank]
        inverse = pow(a[rank][c] % prime, -1, prime)
        for i in range(rank+1,len(a)):
            z = a[i][c]*inverse % prime
            for j in range(c,len(a[0])):
                a[i][j] = (a[i][j]-z*a[rank][j]) % prime
        rank += 1
    return rank


if __name__ == '__main__':
    rng = random.Random(142)
    for _ in range(200):
        n = rng.randrange(1,9)
        a = [[rng.randrange(-3,4) for j in range(n)] for i in range(rng.randrange(1,12))]
        assert len(module.rref(a,n)) == modrank(a)
    d = json.loads(Path(sys.argv[1]).read_text())
    r = json.loads(Path(sys.argv[2]).read_text())['result']
    certificate = json.loads(Path(sys.argv[3]).read_text())
    # Independent role-incidence accumulation (no learner audit import).
    equations = set()
    by_fold = []
    for cfg, selected in zip(d['configurations'],r['selected']):
        by_role = [dict() for _ in r['weightsByRole']]
        for index in selected:
            o = cfg['occurrences'][index]
            roles = r['roleOfSite'][d['types'][o['type']]['offset']:]
            for atom,role in zip(o['ids'],roles):
                by_role[role][atom] = by_role[role].get(atom,0)+1
        local = {tuple(counts.get(atom,0) for counts in by_role) for atom in range(cfg['atoms'])}
        equations.update(local)
        by_fold.append(local)
    assert equations == set(map(tuple,certificate['equations']))
    rank = modrank(sorted(equations))
    assert rank == certificate['rank']
    vectors = [list(map(F,v['vector'])) for v in certificate['nullspaceDirections']]
    assert len(vectors) == len(r['weightsByRole'])-rank
    for v in vectors:
        assert all(sum(x*y for x,y in zip(row,v)) == 0 for row in equations)
    free = certificate['freeRoles']
    assert [[v[j] for j in free] for v in vectors] == [[F(i==j) for j in range(len(free))] for i in range(len(free))]
    for row in certificate['leaveOneConfigurationOut']:
        subset = set().union(*(s for i,s in enumerate(by_fold) if i != row['excluded']))
        assert modrank(sorted(subset)) == row['rank']
    print(json.dumps({'syntheticTests':200, 'independentlyRebuiltEquations':len(equations),
                      'modularRankLowerBound':rank, 'rationalNullityCertificate':len(vectors),
                      'exactRankCertified':rank}))
