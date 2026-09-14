import importlib.util
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('match',Path(__file__).with_name('rigid-cluster-match.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=np.random.default_rng(19)
for n in (4,12,29):
    x=rng.normal(size=(n,3));q,_=np.linalg.qr(rng.normal(size=(3,3)))
    if np.linalg.det(q)<0:q[:,0]*=-1
    y=(x@q+[3,7,-4])[rng.permutation(n)]
    fit=m.match(x,y,1e-8);assert fit is not None and fit['residual']<1e-10
x=np.array([[0.,0,0],[1,0,0],[.2,1.3,0],[.4,.2,2.1]])
assert m.match(x,x*[-1,1,1],1e-8) is None
assert m.match(x,x*1.2,.01) is None
print('Proper rotations/permutations for 4,12,29 sites; reflection and distortion controls passed.')
