"""Independent least-squares and partition controls for the t learner."""
import importlib.util
import random
from pathlib import Path
import numpy as np

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

learner=load('learner','learn-context-point-weights.py')
geometry=load('geometry','audit-anchor-neighborhoods.py')
for n,bell in enumerate([1,1,2,5,15,52,203]):
    parts=list(learner.partitions(list(range(n))))
    assert len(parts)==bell
    canonical={tuple(sorted(p)) for p in parts}
    assert len(canonical)==bell
rng=random.Random(62831)
for trial in range(300):
    n=rng.randrange(1,9)
    pairs=[(u,v) for u in range(n) for v in range(u,n) if rng.random()<.35]
    weights,components=learner.fit_pair_weights(pairs)
    ids=sorted(weights)
    if not ids:continue
    index={v:k for k,v in enumerate(ids)}
    A=np.zeros((len(pairs),len(ids)))
    for r,(u,v) in enumerate(pairs):
        A[r,index[u]]+=1
        A[r,index[v]]+=1
    numerical,_,rank,_=np.linalg.lstsq(A,np.ones(len(pairs)),rcond=None)
    assert np.max(np.abs(numerical-np.array([float(weights[k]) for k in ids])))<1e-10
    assert len(ids)-rank==sum(c['freeParameters'] for c in components)
P=np.zeros((4,3))
V=np.array([[1,0,0],[1,0,0],[-1,0,0],[-1,0,0]])
part=learner.partition_group(P,V,geometry.common_ball)
assert part['status']=='unique-minimum' and part['minimumPoints']==2
assert {tuple(p['indices']) for p in part['points']}=={(0,1),(2,3)}
# Markings determine the split here; identity/order does not.
perm=[2,0,3,1]
changed=learner.partition_group(P[perm],V[perm],geometry.common_ball)
assert {tuple(sorted(perm[j] for j in p['indices'])) for p in changed['points']}=={(0,1),(2,3)}
assert learner.partition_group(np.zeros((9,3)),np.zeros((9,3)),geometry.common_ball)['status']=='unknown-size-budget'
print('Passed Bell partition counts, 300 independent minimum-norm/rank controls, mark-based splitting, relabeling and size-budget controls')
