"""Shared three-site geometry dictionary; known periodic-quotient occurrences only.

All distinct three-atom supports containing a two-edge path below a data-scaled
radius are proposed. Proper rigid fits identify types. Template self-matches tie
symmetry-equivalent site weights. The same dictionary is tested separately and
jointly on the six inputs. No phase, chemistry, target copying, or growth claim.
"""
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from ase import Atoms
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, hstack, eye

HERE = Path(__file__).parent
def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    out = importlib.util.module_from_spec(spec); spec.loader.exec_module(out)
    return out
geom = module('geometry', 'ice-motif-dictionary.py')
marks = module('markings', 'presearch-markings.py')
PERMS = np.array(list(itertools.permutations(range(3))))

def rational_polish(A, rhs, approximate):
    """Exact sparse elimination; use rounded LP values only for free variables."""
    pivots={}
    for i in range(A.shape[0]):
        r=A.getrow(i); row={int(j):Fraction(int(v)) for j,v in zip(r.indices,r.data) if v}
        target=Fraction(int(rhs[i]))
        while row:
            p=min(row)
            if p not in pivots:
                v=row[p];pivots[p]=({j:x/v for j,x in row.items()},target/v);break
            old,b=pivots[p];v=row[p]
            for j,x in old.items():
                row[j]=row.get(j,Fraction(0))-v*x
                if not row[j]:del row[j]
            target-=v*b
        else:
            if target:return None
    x=[Fraction(float(v)).limit_denominator(1000000) for v in approximate]
    for p,(row,b) in sorted(pivots.items(),reverse=True):
        x[p]=b-sum(v*x[j] for j,v in row.items() if j!=p)
    return x

def solve(types, configurations):
    n = 3 * len(types)
    groups = []
    for c in configurations:
        local = [[] for _ in range(c['atoms'])]
        for o in c['occurrences']:
            for u, p in enumerate(o['permutation']):
                local[o['ids'][p]].append(3*o['type']+u)
        groups.extend(local)
    rows=[]; cols=[]; vals=[]
    for p, group in enumerate(groups):
        for v in group: rows.append(p); cols.append(v); vals.append(1)
    rhs=[1]*len(groups); row=len(groups)
    for t in types:
        for a,b in t['symmetryTies']:
            rows.extend([row,row]);cols.extend([3*t['id']+a,3*t['id']+b]);vals.extend([1,-1])
            rhs.append(0);row+=1
    A=coo_matrix((vals,(rows,cols)),shape=(row,n)).tocsr()
    active=sorted({v for g in groups for v in g})
    A=A[:,active]; k=len(active)
    result=linprog([0]*k+[-1], A_eq=hstack([A,coo_matrix((row,1))]), b_eq=rhs,
        A_ub=hstack([-eye(k),np.ones((k,1))]), b_ub=np.zeros(k), bounds=[(0,1)]*(k+1),method='highs')
    out={'configurations':[c['file'] for c in configurations], 'activeVariables':k,
         'requiredPoints':len(groups),'solverStatus':result.message,'status':'unknown'}
    if not result.success:
        out['status']='numerical restricted LP infeasibility' if result.status==2 else 'unknown'
        return out
    w=[Fraction(float(x)).limit_denominator(1000000) for x in result.x[:-1]]
    polished=False
    if any(sum(Fraction(int(v))*w[int(j)] for j,v in zip(A.getrow(i).indices,A.getrow(i).data))!=rhs[i]
           for i in range(A.shape[0])):
        exact_candidate=rational_polish(A,rhs,result.x[:-1])
        if exact_candidate is not None:w=exact_candidate;polished=True
    full=[Fraction(0)]*n
    for v,x in zip(active,w):full[v]=x
    exact=all(sum(full[v] for v in g)==1 for g in groups)
    sym=all(full[3*t['id']+a]==full[3*t['id']+b] for t in types for a,b in t['symmetryTies'])
    out.update(minimumWeight=float(min(w)),exactFilling=exact,exactSymmetry=sym,rationalPolished=polished)
    if not exact or not sym or min(w)<=0:
        out['status']='rational or positive-support gate failed';return out
    equality=groups+[[3*t['id']+a,3*t['id']+b] for t in types for a,b in t['symmetryTies']]
    labels=marks.equality_labels(n,equality)
    out.update(status='exact finite-quotient precheck passed',weights=list(map(str,full)),
        labels=labels,activeScalarClasses=len({labels[v] for v in active}))
    return out

def propose_supports(c, radius_override=None):
    atoms=Atoms('B'*c['atoms'],positions=c['positions'],cell=c['cell'],pbc=True)
    vectors=atoms.get_all_distances(mic=True,vector=True)
    distances=np.linalg.norm(vectors,axis=2);np.fill_diagonal(distances,np.inf)
    radius=float(np.median(distances.min(axis=1)))*1.35 if radius_override is None else float(radius_override)
    supports={}
    for a in range(len(atoms)):
        for b,d in itertools.combinations(np.flatnonzero(distances[a]<=radius).tolist(),2):
            ids=tuple(sorted((a,b,d)))
            if ids not in supports:
                lifted={a:atoms.positions[a],b:atoms.positions[a]+vectors[a,b],d:atoms.positions[a]+vectors[a,d]}
                supports[ids]=np.array([lifted[i] for i in ids])
    return radius,supports

def main():
    raw=Path(sys.argv[1]).read_bytes(); inputs=json.loads(raw)['results']
    epsilon=float(sys.argv[3]) if len(sys.argv)>3 else .05
    types=[]; configs=[]
    for c in inputs:
        radius,supports=propose_supports(c)
        occurrences=[]
        for ids,positions in sorted(supports.items()):
            lengths=np.sort([np.linalg.norm(positions[a]-positions[b]) for a,b in ((0,1),(0,2),(1,2))])
            found=None
            for t in types:
                if np.max(np.abs(lengths-t['lengths']))>2*epsilon:continue
                fit=geom.fit(t['positions'],positions,PERMS,epsilon)
                if fit is not None:found=(t,fit);break
            if found is None:
                center=positions.mean(axis=0);template=positions-center
                ties=set()
                for perm in PERMS:
                    if geom.fit(template,template,np.array([perm]),epsilon) is not None:
                        ties.update(tuple(sorted((u,int(v)))) for u,v in enumerate(perm) if u!=v)
                t={'id':len(types),'positions':template.tolist(),'lengths':lengths.tolist(),
                   'symmetryTies':sorted(ties),'trainingOccurrences':0}
                types.append(t)
                found=(t,dict(permutation=[0,1,2],rotationRow=np.eye(3).tolist(),translation=center.tolist(),residual=0.))
            t,fit=found;t['trainingOccurrences']+=1
            occurrences.append({'ids':ids,'type':t['id'],'liftedPositions':positions.tolist(),**fit})
        config={'file':c['file'],'atoms':c['atoms'],'radius':radius,'occurrences':occurrences}
        configs.append(config)
        print(json.dumps({'file':c['file'],'supports':len(occurrences),'typesSoFar':len(types)}),flush=True)
    results=[solve(types,[c]) for c in configs]+[solve(types,configs)]
    for r in results:print(json.dumps({k:v for k,v in r.items() if k not in ('weights','labels')}),flush=True)
    with open(sys.argv[2],'x') as out:json.dump({'scope':__doc__,'inputHash':hashlib.sha256(raw).hexdigest(),
        'epsilonAngstrom':epsilon,'radiusScale':1.35,'conditionMatchedEnsemble':False,
        'types':types,'configurations':configs,'results':results},out)
if __name__=='__main__':main()
