"""Enumerate species-preserving proper Procrustes self-maps of learned bases.

Keep both component supports and t values; endpoint swapping is explicit.
Numerically exact self-maps and tolerance-feasible proposals are separate.
Approximate self-maps do not form a certified symmetry group. Rank-deficient
bases and continuous maximum-error pose completeness remain separate issues.
"""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

def self_maps(base,tolerance):
    x=np.asarray(base['anchors']);center=x.mean(axis=0);xc=x-center
    rank=int(np.linalg.matrix_rank(xc,tol=1e-10))
    groups=defaultdict(list)
    for i,s in enumerate(base['species']):groups[s].append(i)
    parts=[list(itertools.permutations(ids)) for ids in groups.values()]
    if np.prod([len(p) for p in parts])>100000:raise ValueError('Permutation budget exceeded; no completeness claim')
    components=[set(p) for p in base['componentSites']];rows=[];tested=0
    for images in itertools.product(*parts):
        p=list(range(len(x)))
        for ids,targets in zip(groups.values(),images):
            for i,j in zip(ids,targets):p[i]=j
        if any(base['t'][i]!=base['t'][j] for i,j in enumerate(p)):continue
        mapped=[{p[i] for i in part} for part in components]
        if any(part not in components for part in mapped):continue
        endpoint_map=[components.index(part) for part in mapped];tested+=1
        y=xc[p];u,_,vt=np.linalg.svd(xc.T@y);fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vt);rotation=u@fix@vt
        error=float(np.linalg.norm(xc@rotation-y,axis=1).max())
        if error<=tolerance+1e-10:
            rows.append(dict(permutation=p,rotationRow=rotation.tolist(),translation=(center-center@rotation).tolist(),
                             endpointMap=endpoint_map,maxResidualAngstrom=error,numericallyExact=error<=1e-8))
    return dict(rank=rank,permutationsTested=tested,maps=rows)

if __name__=='__main__':
    source,output=map(Path,sys.argv[1:]);library=json.loads(source.read_text());rows=[]
    for i,b in enumerate(library['baseMotifs']):rows.append(dict(base=i,**self_maps(b,library['positionToleranceAngstrom'])))
    result=dict(scope=__doc__,libraryHash=hashlib.sha256(source.read_bytes()).hexdigest(),
                codeHash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),positionToleranceAngstrom=library['positionToleranceAngstrom'],
                results=rows,summary=dict(bases=len(rows),rankBelowTwo=sum(r['rank']<2 for r in rows),
                    basesWithNonidentityExact=sum(any(m['numericallyExact'] and m['permutation']!=list(range(len(m['permutation']))) for m in r['maps']) for r in rows),
                    basesWithNonidentityApproximate=sum(any(not m['numericallyExact'] for m in r['maps']) for r in rows),
                    exactMaps=sum(m['numericallyExact'] for r in rows for m in r['maps']),proposedMaps=sum(len(r['maps']) for r in rows)),
                limits='Finite species-preserving Procrustes proposals, not complete continuous feasible poses or exact algebraic symmetry certificates. Stored support and component partition only; no markings are merged and no search rules are changed.')
    with output.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result['summary']))
