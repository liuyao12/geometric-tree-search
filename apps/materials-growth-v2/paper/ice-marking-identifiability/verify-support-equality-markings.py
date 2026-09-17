"""Reconstruct m-equality graph from source coordinates, not learner links."""
import hashlib
import itertools
import json
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree

coordp,dictp,libp,supportp,markp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coords,dictionary,library,support,mark=[json.loads(p.read_text()) for p in [coordp,dictp,libp,supportp,markp]]
assert mark['supportHash']==sha(supportp)
for p in [coordp,dictp,libp]:assert support['sourceHashes'][p.name]==sha(p)
cc={c['id']:c for c in coords['configurations']};dd={r['id']:r for r in dictionary['configurations']}
bytype=defaultdict(list)
for i,a in enumerate(support['anchors']):bytype[a['type']].append((i,a))
n=len(support['anchors']);values=mark['values'];assert len(values)==n and all(isinstance(v,int) for v in values)
edges=set();sites=0;maxerror=0.;frames=0
for reg in library['trainingRegistrations']:
    if reg['id'] not in support['trainingFrames'] or reg['coverVariant']!='original':continue
    frames+=1;cid=reg['id'];c=cc[cid];cell=np.asarray(c['cell']);inv=np.linalg.inv(cell)
    tol=support['positionTolerance'];assert np.linalg.svd(cell,compute_uv=False)[-1]>tol
    pos=(np.asarray(c['positions'])@inv%1)@cell
    shifts=np.asarray(list(itertools.product([-1,0,1],repeat=3)))@cell
    trees={}
    for species in set(c['species']):
        ids=np.flatnonzero(np.asarray(c['species'])==species)
        cloud=(pos[ids,None,:]+shifts[None,:,:]).reshape(-1,3)
        trees[species]=cKDTree(cloud),np.repeat(ids,27),cloud
    at=defaultdict(list)
    for chosen in reg['selected']:
        o=dd[cid]['occurrences'][chosen['edge']];R=np.asarray(o['rotationRow']);tr=np.asarray(o['translation'])
        assert np.max(np.abs(R.T@R-np.eye(3)))<1e-8 and abs(np.linalg.det(R)-1)<1e-8
        for index,a in bytype[o['type']]:
            x=((np.asarray(a['position'])@R+tr)@inv%1)@cell
            tree,ids,cloud=trees[a['species']];hits=tree.query_ball_point(x,tol+1e-9);assert len(hits)==1
            atom=int(ids[hits[0]]);at[atom].append(index)
            maxerror=max(maxerror,float(np.linalg.norm(cloud[hits[0]]-x)))
    assert len(at)==len(pos);sites+=len(at)
    for group in at.values():
        assert len({values[i] for i in group})==1,'Observed marking disagreement'
        edges.update(itertools.combinations(sorted(set(group)),2))
assert edges=={tuple(e) for e in mark['observedEqualityEdges']},'Equality edges do not replay'
adj=[set() for _ in range(n)]
for a,b in edges:adj[a].add(b);adj[b].add(a)
classes=[];seen=set()
for i in range(n):
    if i in seen:continue
    stack=[i];component=[]
    while stack:
        j=stack.pop()
        if j in seen:continue
        seen.add(j);component.append(j);stack.extend(adj[j]-seen)
    classes.append(component)
assert len(classes)==mark['freeEqualityClasses'] and n-len(classes)==mark['equationRank']
assert len({values[c[0]] for c in classes})==len(classes),'Code merges distinguishable classes'
for group in classes:assert len({values[i] for i in group})==1
weights=[Fraction(a['t']).limit_denominator(1000000) for a in support['anchors']]
assert all(0<w<=1 for w in weights)
t_compatible=conflicts=0
for a,b in itertools.combinations_with_replacement(range(n),2):
    if support['anchors'][a]['species']!=support['anchors'][b]['species'] or weights[a]+weights[b]>1:continue
    t_compatible+=1;conflicts+=values[a]!=values[b]
report=dict(markingHash=sha(markp),supportHash=sha(supportp),verifierHash=sha(Path(__file__)),
            frames=frames,atomicSites=sites,anchorCount=n,verifiedEqualityEdges=len(edges),
            equalityClasses=len(classes),rank=n-len(classes),classSizes=sorted(map(len,classes),reverse=True),
            isolatedAnchors=[dict(index=c[0],t=support['anchors'][c[0]]['t']) for c in classes if len(c)==1],
            speciesAndCapacityCompatibleAnchorPairs=t_compatible,markingConflictsOnCompatiblePairs=conflicts,
            redundancyCertified=conflicts==0,
            redundancyAssumptions='Scalar invariant values only on positive t-support; species-preserving correspondences; no extended marking-only anchors. Then every pair in any t-legal overlap agrees, so m adds no filtering.',
            maxPositionErrorAngstrom=maxerror,
            limits='Exact combinatorial rank after tolerance-based source replay. Scalar invariant action, one m per learned t-anchor, supplied poses. No evidence of incorrect physical connections or of general GCTS impossibility. More channels with the same identity action obey the same component equalities.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
