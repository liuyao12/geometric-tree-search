"""Periodic contact enumeration and sound necessary-consistency controls."""
import importlib.util,itertools,random
from pathlib import Path
import numpy as np
from ase.geometry import find_mic

spec=importlib.util.spec_from_file_location('contacts',Path(__file__).with_name('propose-unseeded-anchor-contacts.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rng=np.random.default_rng(75216)
for trial in range(20):
    cell=np.array([[2.,0,0],[.7,2.3,0],[.2,.9,2.8]])
    P=rng.uniform(-2,3,(25,3))@cell
    actual,bound=module.nearby(P,cell)
    expected=[]
    for i in range(len(P)):
        d,_=find_mic(P[i+1:]-P[i],cell,pbc=True)
        expected.extend((i,i+1+j) for j,length in enumerate(np.linalg.norm(d,axis=1)) if length<=.30+1e-9)
    assert actual==expected and bound['status']=='image-bound-verified'

rng=random.Random(2971)
solutions=0
for trial in range(200):
    supports=[dict(cluster=k) for k in range(3) for p in range(4)]
    candidates=[dict(cluster=k,supports=sorted(rng.sample(list(range(4*k,4*k+4)),2))) for k in range(3) for option in range(2)]
    contacts=[dict(supports=[i,j]) for i in range(12) for j in range(i+1,12) if rng.random()<.2]
    reduced=module.prune_contacts(candidates,supports,contacts)
    def covers(remaining,chosen):
        if not remaining:
            yield chosen;return
        first=min(remaining)
        for ei,c in enumerate(contacts):
            block=set(c['supports'])
            if first in block and block<=remaining:
                yield from covers(remaining-block,chosen+[ei])
    for selected in itertools.product([0,1],[2,3],[4,5]):
        ports={s for ci in selected for s in candidates[ci]['supports']}
        for cover in covers(ports,[]):
            assert set(selected)<=set(reduced['candidates'])
            assert set(cover)<=set(reduced['contacts'])
            solutions+=1
print(f'Passed 20 independent periodic-neighbor comparisons and 200 exhaustive consistency controls preserving {solutions} covers')
