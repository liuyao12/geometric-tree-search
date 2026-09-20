import importlib.util,itertools
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('enum',Path(__file__).with_name('enumerate-rigid-proposals.py'));enum=importlib.util.module_from_spec(spec);spec.loader.exec_module(enum)
X=np.concatenate([np.eye(3),-np.eye(3)])
poses,stats=enum.enumerate_poses(X,X,['X']*6,1e-8)
assert len(poses)==24 and not stats['truncated']
assert len({tuple(p['permutation']) for p in poses})==24
for p in poses:assert abs(np.linalg.det(p['rotationRow'])-1)<1e-8
print('All 24 proper octahedral maps found')
rng=np.random.default_rng(719)
for case in range(6):
    X=rng.normal(size=(6,3));Y=X+rng.normal(scale=.03,size=X.shape);expected=set()
    for perm in itertools.permutations(range(6)):
        Q=Y[list(perm)];xc=X-X.mean(axis=0);yc=Q-Q.mean(axis=0)
        U,S,V=np.linalg.svd(xc.T@yc);R=U@np.diag([1,1,np.linalg.det(U@V)])@V
        if max(np.linalg.norm(xc@R-yc,axis=1))<=.15+1e-10:expected.add(perm)
    poses,stats=enum.enumerate_poses(X,Y,['X']*6)
    assert not stats['truncated'] and {tuple(p['permutation']) for p in poses}==expected
print('Six cases agree with exhaustive 720-correspondence checks')
X=np.array([[0,0,0],[1,0,0],[0,2,0],[0,0,3]],dtype=float);Y=X*np.array([-1,1,1])
poses,stats=enum.enumerate_poses(X,Y,['A','B','C','D'],1e-8);assert not poses and not stats['truncated']
poses,stats=enum.enumerate_poses(X,X,['A','B','C','D'],max_nodes=1);assert stats['truncated']
poses,stats=enum.enumerate_poses([[0,0,0],[1,0,0]],[[0,0,0],[1,0,0]],['X','X']);assert stats['templateRank']==1
print('Reflection rejected; budget and collinear rank limits explicit')
