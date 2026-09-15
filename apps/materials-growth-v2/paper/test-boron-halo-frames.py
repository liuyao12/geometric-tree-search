import importlib.util
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('halo',Path(__file__).with_name('boron-halo-proposals.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
rng=np.random.default_rng(303)
for _ in range(40):
    points=rng.normal(size=(9,3));u,_,vt=np.linalg.svd(rng.normal(size=(3,3)));q=u@vt
    if np.linalg.det(q)<0:u[:,-1]*=-1;q=u@vt
    shift=rng.normal(size=3);observed=points@q+shift
    fitted,t,error=h.frame(points,observed)
    assert error<1e-12 and np.max(np.abs(fitted-q))<1e-12 and np.max(np.abs(t-shift))<1e-12
    extra=rng.normal(size=(7,3));local=(extra@q+shift-t)@fitted.T
    assert np.max(np.abs(local-extra))<1e-12
    order=rng.permutation(len(points));rp,tp,ep=h.frame(points[order],observed[order])
    assert ep<1e-12 and np.max(np.abs(rp-fitted))<1e-12 and np.max(np.abs(tp-t))<1e-12
try:h.frame([[-1,0,0],[1,0,0]],[[-1,0,0],[1,0,0]])
except AssertionError:pass
else:raise AssertionError('axial gauge silently fixed')
print({'properRigidTransformCases':40,'correspondencePermutationCases':40,'rankDeficientFrameRejected':True})
