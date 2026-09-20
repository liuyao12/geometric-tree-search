import importlib.util,itertools
from pathlib import Path
import numpy as np
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load('periodic','periodic-interface-proposals.py');csp=load('shared','check-shared-interface-poses.py')
assert p.graph_audit(2,[(0,1,[0,0,0])])['components'][0]['translationRank']==0
assert p.graph_audit(1,[(0,0,[1,0,0]),(0,0,[0,1,0]),(0,0,[0,0,1])])['connectedPeriodicLift']
r=p.graph_audit(1,[(0,0,[2,0,0]),(0,0,[0,1,0]),(0,0,[0,0,1])]);assert not r['connectedPeriodicLift'] and r['components'][0]['latticeIndex']==2
assert p.graph_audit(1,[(0,0,[1,0,0]),(0,0,[0,1,0])])['components'][0]['translationRank']==2
cube=p.propose([[.2,.3,.4]],np.eye(3)*2);assert len(cube['edges'])==3 and cube['graph']['connectedPeriodicLift']
larger=p.propose([[.2,.3,.4]],np.eye(3)*2,start_shell=cube['shell']+1);assert larger['edges']==cube['edges']
cell=np.array([[3.,0,0],[.2,3.4,0],[.3,.1,3.8]]);centers=np.array([[.1,.2,.3],[.7,.6,.8]])@cell
theta=.7;R=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1]])
a=p.propose(centers,cell);b=p.propose(centers@R+[.37,-.16,.28],cell@R)
assert a['graph']['connectedPeriodicLift'] and b['graph']['connectedPeriodicLift']
def lengths(result,cell):
    q=np.asarray(result['wrappedCenters']);return sorted(float(np.linalg.norm(q[j]+np.asarray(s)@cell-q[i])) for i,j,s in result['edges'])
assert np.allclose(lengths(a,cell),lengths(b,cell@R),atol=1e-8)
assert p.propose(centers,cell,start_shell=a['shell']+1)['edges']==a['edges']
print('Periodic fragments, rank-2 layer, index-2 sublattice, self-image cubic edges, enlarged image box and rigid-motion controls passed')
independent=load('independent','verify-shared-interface-poses.py')
assert len(independent.periodic_paths(1,[(0,0,[1,0,0]),(0,0,[0,1,0]),(0,0,[0,0,1])]))==4
try:independent.periodic_paths(1,[(0,0,[2,0,0]),(0,0,[0,1,0]),(0,0,[0,0,1])])
except AssertionError:pass
else:raise AssertionError('Incorrectly certified an index-two periodic graph')
print('Independent constructive paths accept the full lattice and reject an index-two sublattice')
domains=[[0,1]]*3;relations=[(0,1,{(0,0),(1,1)}),(1,2,{(0,0),(1,1)}),(0,2,{(0,1),(1,0)})]
solution,stats=csp.solve(domains,relations);assert solution is None and stats['status']=='exhausted-saved-pose-domain'
_,stats=csp.solve(domains,relations,limit=1);assert stats['status']=='unknown-budget'
rng=np.random.default_rng(720)
for _ in range(100):
    domains=[[0,1,2]]*4;relations=[(a,b,{(i,j) for i in range(3) for j in range(3) if rng.random()<.5}) for a,b in itertools.combinations(range(4),2)]
    expected=any(all((values[a],values[b]) in allowed for a,b,allowed in relations) for values in itertools.product(range(3),repeat=4))
    solution,stats=csp.solve(domains,relations);assert (solution is not None)==expected
print('Shared-pose CSP agrees with exhaustive enumeration on 100 controls; budget is unknown')
