"""Proper-rotation and endpoint-decoration controls for junction matching."""
import importlib.util
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

spec=importlib.util.spec_from_file_location('junction',Path(__file__).with_name('boron-junction-learning.py'))
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
rng=np.random.default_rng(171);positives=0;mirrors=0
for trial in range(100):
    n=3+trial%4;points=rng.normal(size=(n,3));colors=[[i,2,2,0,0] for i in range(n)]
    rotation=Rotation.random(random_state=rng).as_matrix();permutation=rng.permutation(n)
    target=(points@rotation)[permutation];target_colors=[colors[i] for i in permutation]
    fit=j.match(points,colors,target,target_colors,1e-7);assert fit is not None;positives+=1
    reflected=points@np.diag([-1,1,1]);assert j.match(points,colors,reflected,colors,1e-7) is None;mirrors+=1
    bad=[c.copy() for c in target_colors];bad[0][1]=3
    assert j.match(points,colors,target,bad,1e-7) is None
# A one-vector star has a continuous axial stabilizer; it must still be matchable.
assert j.match([[1,0,0]],[[0,2,2,0,0]],[[0,0,1]],[[0,2,2,0,0]],1e-7) is not None
print({'properRotationPermutationTests':positives,'chiralReflectionsRejected':mirrors,'decorationMutationsRejected':100,'rankOneRotation':True})
