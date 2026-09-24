import pickle,itertools,json
from collections import defaultdict
import sys,importlib.util,pathlib
if len(sys.argv)>1:
 p=pickle.load(open(sys.argv[1],'rb')) # Optional trusted local cache only.
else:
 spec=importlib.util.spec_from_file_location('corona',pathlib.Path(__file__).with_name('search-nonacube-two-corona.py'))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);p=m.build()
# Different enumeration: exhaust a translation box derived from support bounds,
# checking voxel contact directly, rather than aligning every target/anchor.
S=[]
for normal in [2,1,0]:
 axes=[a for a in range(3) if a!=normal]
 S.append({tuple(d if i==axis else 0 for i in range(3)) for axis in axes for d in [-2,-1,0,1,2]})
R=S[0];halo=lambda V:{tuple(q[i]+d[i] for i in range(3)) for q in V for d in itertools.product([-1,0,1],repeat=3)}
near=halo(R)-R
placed=lambda oi,t:{tuple(q[i]+t[i] for i in range(3)) for q in S[oi]}
A=set();U=set()
for oi in range(3):
 for t in itertools.product(range(-5,6),repeat=3):
  c=placed(oi,t)
  if not c&R and c&near:A.add((oi,t))
assert A==p['first']
required=near.copy()
for oi,t in A:required.update(halo(placed(oi,t))-R-placed(oi,t))
for oi in range(3):
 for t in itertools.product(range(-10,11),repeat=3):
  c=placed(oi,t)
  if not c&R and c&required:U.add((oi,t))
assert U==set(p['universe'])
print(json.dumps({'independentBoxEnumeration':True,'first':len(A),'allCandidates':len(U)}))
