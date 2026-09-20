"""Adversarial checks for learned off-atom pair interfaces."""
import copy,importlib.util,json,sys,tempfile
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('learner',Path(__file__).with_name('learn-offatom-interfaces.py'))
learner=importlib.util.module_from_spec(spec);spec.loader.exec_module(learner)
rng=np.random.default_rng(719);xa=np.array([.3,-.8,1.2]);xb=np.array([-.7,.2,.6]);observations=[]
for _ in range(8):
    rotations=[]
    for k in range(2):
        Q,_=np.linalg.qr(rng.normal(size=(3,3)));Q[:,0]*=np.linalg.det(Q);rotations.append(Q)
    A,B=rotations;observations.append(dict(RA=A,RB=B,d=xa@A-xb@B))
fitted=learner.fit(observations)
assert fitted['positionRank']==6 and np.linalg.norm(np.asarray(fitted['anchorA'])-xa)<1e-10 and np.linalg.norm(np.asarray(fitted['anchorB'])-xb)<1e-10
assert learner.fit(observations[:1])['positionRank']==3
print('Recovered free non-midpoint anchors; single-pose underdetermination recorded')
spec=importlib.util.spec_from_file_location('checker',Path(__file__).with_name('verify-offatom-interfaces.py'))
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
coord,meta,motifs,result=map(Path,sys.argv[1:]);original=json.loads(result.read_text());checker.verify(coord,meta,motifs,result)
def corrupt(name,edit):
    data=copy.deepcopy(original);edit(data)
    with tempfile.TemporaryDirectory(prefix='gcts-interface-control-') as directory:
        path=Path(directory)/'corrupt.json';path.write_text(json.dumps(data))
        try:checker.verify(coord,meta,motifs,path)
        except (AssertionError,ValueError,KeyError,IndexError):print('Rejected:',name)
        else:raise AssertionError('Accepted corruption: '+name)
corrupt('moved anchor',lambda d:d['models'][0]['anchorA'].__setitem__(0,50.))
corrupt('changed marking',lambda d:d['models'][0]['valueB'].__setitem__(0,50.))
corrupt('invented recurrence',lambda d:d['models'][0].__setitem__('trainingFrames',999))
corrupt('omitted proposed pair',lambda d:d['observations'].pop())
corrupt('altered source displacement',lambda d:d['observations'][0]['d'].__setitem__(0,50.))
print('All interface corruption controls passed')
