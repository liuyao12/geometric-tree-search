"""Joint connection geometry must be covariant but detect a relative twist."""
import copy
import importlib.util
from pathlib import Path
import numpy as np

def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

joint=load('boron-junction-joined');learner=load('boron-junction-learning')
color=[12,2,2,0,0]
def node(items):return {'incident':[{'candidate':cid,'vector':vec,'color':color[:]} for cid,vec in items]}
left=node([(0,[3.,0.,0.]),(1,[.2,1.,0.]),(2,[.1,.3,1.7])])
right=node([(0,[-3.,0.,0.]),(3,[.4,1.2,.7]),(4,[-.3,.2,1.9])])
sa={'candidates':[0,1,2]};sb={'candidates':[0,3,4]}
p,c=joint.joined(left,sa,right,sb,0);rng=np.random.default_rng(812)
for trial in range(100):
    u,_,vt=np.linalg.svd(rng.normal(size=(3,3)));fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vt);rot=u@fix@vt
    a,b=copy.deepcopy(left),copy.deepcopy(right)
    for n in (a,b):
        for e in n['incident']:e['vector']=(np.array(e['vector'])@rot).tolist()
        rng.shuffle(n['incident'])
    aa={'candidates':rng.permutation(sa['candidates']).tolist()};bb={'candidates':rng.permutation(sb['candidates']).tolist()}
    q,qc=joint.joined(a,aa,b,bb,0);fit=learner.match(p,c,q,qc,.03)
    assert fit is not None and joint.fit_valid(p,q,fit,.03)
twist=np.array([[1.,0.,0.],[0.,0.,-1.],[0.,1.,0.]])
b=copy.deepcopy(right)
for e in b['incident']:e['vector']=(np.array(e['vector'])@twist).tolist()
q,qc=joint.joined(left,sa,b,sb,0)
assert learner.match([e['vector'] for e in right['incident']],[color]*3,[e['vector'] for e in b['incident']],[color]*3,.03) is not None
assert learner.match(p,c,q,qc,.03) is None
reflected=np.asarray(p)@np.diag([-1.,1.,1.]);assert learner.match(p,c,reflected,c,.03) is None
print('100 rotation/permutation controls passed; independent-star twist and chiral reflection rejected')
