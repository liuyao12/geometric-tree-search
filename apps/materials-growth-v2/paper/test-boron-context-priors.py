"""Feature-renumbering invariance and withheld-target-label controls."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
spec=importlib.util.spec_from_file_location('p',Path(__file__).with_name('boron-context-priors.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
d=json.loads(Path(sys.argv[1]).read_text());learning=json.loads(Path(sys.argv[2]).read_text())
hashes=p.context_hashes(d,learning);folds=p.fit(d,learning)
renumbered=copy.deepcopy(d)
for c in renumbered['configurations']:
    for o in c['occurrences']:o['ids']=[f'opaque-{1000000-x}' for x in o['ids']]
assert p.context_hashes(renumbered,learning)==hashes
reversed_data=copy.deepcopy(d)
for c in reversed_data['configurations']:c['occurrences'].reverse()
assert p.context_hashes(reversed_data,learning)==[list(reversed(h)) for h in hashes]
for i,fold in enumerate(folds):
    mutated=copy.deepcopy(learning);mutated['result']['selected'][i]=[]
    assert p.fit(d,mutated)[i]==fold
print({'atomIdRenumbering':True,'occurrenceOrderInvariance':True,'withheldWitnessMutations':len(folds)})
