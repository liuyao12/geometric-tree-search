"""Registration must tolerate distractors, permutations and proper rotations."""
import importlib.util
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('reg',Path(__file__).with_name('register-portable-geometry.py'))
reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
p=np.array([[3.,0.,0.],[.2,1.,0.],[.1,.3,1.7],[3.4,1.2,.7],[2.7,.2,1.9]])
colors=[[-1],[0,1],[0,1],[1,1],[1,1]];rng=np.random.default_rng(702);fits_checked=0
for trial in range(100):
    u,_,vt=np.linalg.svd(rng.normal(size=(3,3)));fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vt);r=u@fix@vt
    q=p@r+rng.normal(size=p.shape)*.001
    permutation=[0,*rng.permutation(np.arange(1,len(p))).tolist()];q=q[permutation];qc=[colors[i] for i in permutation]
    q=np.concatenate([q,rng.normal(size=(4,3))*5]);qc+=colors[1:]
    answers,truncated=reg.registrations(p,colors,q,qc,.03);assert answers and not truncated
    for fit in answers:
        rotation=np.array(fit['rotationRow']);assert abs(np.linalg.det(rotation)-1)<1e-7
        assert np.max(np.linalg.norm(p@rotation-q[fit['permutation']],axis=1))<=.03000001
        assert all(colors[i]==qc[j] for i,j in enumerate(fit['permutation']));fits_checked+=1
reflected=p@np.diag([-1.,1.,1.]);assert not reg.registrations(p,colors,reflected,colors,.03)[0]
degenerate=np.array([[1.,0,0],[2.,0,0]]);assert reg.registrations(degenerate,[[-1],[0]],degenerate,[[-1],[0]],.03)[1]
octa=np.concatenate([np.eye(3),-np.eye(3)]);delta=np.array([1.,0,0]);symmetric=np.vstack([delta,octa,octa+delta]);sc=[[-1]]+[[0,1]]*6+[[1,1]]*6
symmetry_fits,cut=reg.registrations(symmetric,sc,symmetric,sc,.03);assert len(symmetry_fits)>=4 and not cut
print({'randomCases':100,'acceptedFitsChecked':fits_checked,'properRotationAndDistractorChecks':True,'degenerateFrameFlagged':True,'symmetricRotations':len(symmetry_fits)})
