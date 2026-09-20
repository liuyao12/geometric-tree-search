"""Controls for conservative proximity groups and common-ball witnesses."""
import importlib.util
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-anchor-neighborhoods.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for P in [[[0,0,0]],[[0,0,0],[.3,0,0]],[[0,0,0],[.1,0,0],[.2,0,0]]]:
    r=module.common_ball(P)
    assert r['status']=='common-ball-witness'
    assert max(np.linalg.norm(np.asarray(P)-r['center'],axis=1))<=.15+1e-9
assert module.common_ball([[0,0,0],[.4,0,0]])['status']=='diameter-obstruction'
triangle=np.array([[0,0,0],[.29,0,0],[.145,np.sqrt(3)*.145,0]])
assert np.max(np.linalg.norm(triangle[:,None]-triangle[None,:],axis=2))<.3
assert module.common_ball(triangle)['status']=='unknown-no-ball-witness'
P=np.array([[9.9,0,0],[.1,0,0],[5,0,0]])
groups=module.proximity_groups(P,np.eye(3)*10)
assert [g[0] for g in groups]==[[0,1],[2]]
assert not any(g[2] for g in groups)
assert abs(np.linalg.norm(groups[0][1][1]-groups[0][1][0])-.2)<1e-8
R=np.array([[0.,1.,0.],[-1.,0.,0.],[0.,0.,1.]])
changed=module.proximity_groups(P@R+[1,2,3],np.eye(3)*10@R)
assert [g[0] for g in changed]==[g[0] for g in groups]
chain=module.proximity_groups([[0,0,0],[.2,0,0],[.4,0,0]],np.eye(3)*10)
assert len(chain)==1 and module.common_ball(chain[0][1])['status']=='diameter-obstruction'
print('Passed ball witnesses, diameter, pairwise-without-common-ball, periodic image, rigid motion and nontransitive proximity controls')
