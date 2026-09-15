"""Independent permutation controls and common-witness/rotation tests."""
import importlib.util
from itertools import permutations
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('cloud',Path(__file__).with_name('portable-cloud-markings.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=np.random.default_rng(339);cases=0
for _ in range(200):
    n=int(rng.integers(1,6));a=rng.normal(size=(n,3));b=a+rng.normal(size=(n,3))*.08
    colors=[[int(rng.integers(0,2))] for _ in range(n)];perm=rng.permutation(n)
    ca={'vectors':a.tolist(),'colors':colors};cb={'vectors':b[perm].tolist(),'colors':[colors[i] for i in perm]};radius=.15
    expected=any(all(colors[i]==cb['colors'][p[i]] and np.linalg.norm(a[i]-b[perm[p[i]]])<=radius+1e-10 for i in range(n)) for p in permutations(range(n)))
    assert (m.contains(ca,cb,radius) is not None)==expected
    u,_,vt=np.linalg.svd(rng.normal(size=(3,3)));fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vt);r=u@fix@vt
    assert (m.contains(m.transform(ca,r),m.transform(cb,r),radius) is not None)==expected;cases+=1
def one(x):return {'vectors':[[x,0.,0.]],'colors':[[0]]}
assert m.common_witness([one(0),one(.15)],one(.075),.1)
assert m.common_witness([one(.15),one(.3)],one(.225),.1)
assert m.common_witness([one(0),one(.15),one(.3)],one(.15),.1) is None
assert .3>2*.1  # Endpoint balls are disjoint, despite adjacent pair overlap.
assert m.propose_common_witness([one(0),one(.15)],.1)['status']=='verified-witness'
assert m.propose_common_witness([one(0),one(.15),one(.3)],.1)['status']=='unknown'
# All three pairs overlap, but these equal-radius balls have no common point.
triangle=[{'vectors':[v],'colors':[[0]]} for v in [[0,0,0],[.19,0,0],[.095,.19*np.sqrt(3)/2,0]]]
for i,j in [(0,1),(0,2),(1,2)]:
    midpoint={'vectors':((np.array(triangle[i]['vectors'])+triangle[j]['vectors'])/2).tolist(),'colors':[[0]]}
    assert m.common_witness([triangle[i],triangle[j]],midpoint,.1)
assert m.propose_common_witness(triangle,.1)['status']=='unknown'
# Conversely unknown MUST NOT be used as impossibility: this family intersects.
hard=[one(-1),one(.8),one(.8)]
assert m.common_witness(hard,one(0),1)
assert m.propose_common_witness(hard,1)['status']=='unknown'
try:m.transform(one(1),np.diag([-1.,1.,1.]));raise AssertionError('reflection accepted')
except ValueError:pass
assert m.contains(one(1),{'vectors':[[0,1,0]],'colors':[[0]]},.01) is None
print(f'{cases} exhaustive-bijection and rotation controls passed; no hidden refitting, reflection, or pairwise-chain shortcut')
