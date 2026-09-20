import importlib.util,itertools
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('rigid',Path(__file__).with_name('bounded-rigid-registration.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=np.random.default_rng(7163)
def replay(X,Y,answer,eps):
    R=np.asarray(answer['rotationRow']);tr=np.asarray(answer['translation']);p=answer['permutation']
    assert np.max(np.abs(R.T@R-np.eye(3)))<1e-8 and abs(np.linalg.det(R)-1)<1e-8
    assert max(np.linalg.norm(X@R+tr-Y[p],axis=1))<=eps+1e-9
def exhaustive(X,Y,eps):
    for p in itertools.permutations(range(len(X))):
        Q=Y[list(p)];x=X-X.mean(axis=0);q=Q-Q.mean(axis=0);u,_,vt=np.linalg.svd(x.T@q);D=np.eye(3);D[-1,-1]=np.linalg.det(u@vt);R=u@D@vt
        if np.max(np.linalg.norm(x@R-q,axis=1))<=eps+1e-9:return True
    return False
for n in [8,16,32]:
    X=rng.normal(size=(n,3));R,_=np.linalg.qr(rng.normal(size=(3,3)));R[:,0]*=np.linalg.det(R)
    p=rng.permutation(n);Y=(X@R+np.array([2.,-3.,4.]))[p]
    answer,stats=m.fit(X,Y,['opaque']*n,1e-7);assert answer is not None and not stats['truncated'];replay(X,Y,answer,1e-7)
print('8/16/32-point rotated and permuted clouds verified')
for i in range(12):
    X=rng.normal(size=(6,3));Y=X[rng.permutation(6)]+rng.normal(scale=.01 if i%2 else .3,size=(6,3));eps=.04
    answer,stats=m.fit(X,Y,['same']*6,eps,max_nodes=100000);assert not stats['truncated']
    assert (answer is not None)==exhaustive(X,Y,eps)
    if answer is not None:replay(X,Y,answer,eps)
print('12 cases agree with independent exhaustive correspondence checks')
X=np.array([[0.,0,0],[1,0,0],[0,2,0],[0,0,3]])
answer,stats=m.fit(X,X*np.array([-1,1,1]),['a','b','c','d'],1e-7);assert answer is None and not stats['truncated']
answer,stats=m.fit(X,X,['a','b','c','d'],1e-7,max_nodes=1);assert answer is None and stats['truncated']
print('Chiral reflection rejected; budget stop reported as unknown')
