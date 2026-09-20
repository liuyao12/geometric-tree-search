import importlib.util,itertools,random
from pathlib import Path
spec=importlib.util.spec_from_file_location('solver',Path(__file__).with_name('search-unseeded-contacts.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rng=random.Random(38471)
for trial in range(200):
    candidates=[dict(supports=sorted(rng.sample(list(range(4*k,4*k+4)),2))) for k in range(2) for option in range(2)]
    contacts=[dict(supports=[i,j]) for i in range(8) for j in range(i+1,8) if rng.random()<.2]
    expected=[]
    for chosen in itertools.product([0,1],[2,3]):
        required={p for ci in chosen for p in candidates[ci]['supports']}
        for cover in itertools.combinations(range(len(contacts)),len(required)//2):
            flattened=[p for ei in cover for p in contacts[ei]['supports']]
            if len(flattened)==len(set(flattened)) and set(flattened)==required:expected.append((chosen,cover))
    witness,stats=module.solve(candidates,contacts,[[0,1],[2,3]],list(range(len(contacts))))
    assert bool(expected)==(witness is not None)
    if witness is not None:
        assert (tuple(witness['candidates']),tuple(sorted(witness['contacts']))) in expected
    else:assert stats['status']=='exhausted-finite-context-contact-pool'
_,stats=module.solve([dict(supports=[0])],[],[[0]],[],limit=0)
assert stats['status']=='unknown-budget'
print('Passed 200 independent exhaustive context/contact-cover comparisons and search-budget control')
